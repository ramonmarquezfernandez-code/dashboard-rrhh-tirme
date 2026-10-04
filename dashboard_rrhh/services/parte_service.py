"""Alta, edición y consulta de los partes de trabajo del propio empleado.

ParteValidator aplica las reglas del formulario sin tocar la base de datos (recibe
como parámetros lo que necesita consultar). ParteService calcula los campos que
nunca vienen del cliente (PERNR, periodo, grupo...) y guarda en zparte.
"""
import re
import time
from dataclasses import dataclass, field
from datetime import date

from extensions import db
from models import DepartmentPayroll, EppartStatus, TepClassificationPayroll, UserPayroll, ZParte
from services import parte_campos as campos
from services.calendario import periodo_de, periodo_traspasado, tipo_dia

ESTADO_CREADO_POR_EMPLEADO = 'B'
FORMATO_HORA = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')


class ErrorValidacion(ValueError):
    def __init__(self, errores):
        super().__init__('Revisa los datos del parte.')
        self.errores = errores


class ConflictoParte(ValueError):
    """El parte ya existe o ya no se puede modificar (409)."""


class ParteNoEncontrado(LookupError):
    """El parte no existe o no es del usuario (404)."""


@dataclass
class ParteValidado:
    """Valores ya limpios y calculados, listos para guardar."""
    fecha: date
    turno: str
    tipodia: str
    horas: dict                      # columna de zparte -> int
    motivos: dict                    # columna de motivo -> texto o None
    total_he: int
    presencia_min: int | None
    situacion: str
    marcas: set = field(default_factory=set)
    motivo_sustitucion: str | None = None
    km: int | None = None
    observaciones: str | None = None


def minutos(hora):
    """'HH:MM' -> minutos desde las 00:00."""
    horas, mins = hora.split(':')
    return int(horas) * 60 + int(mins)


def presencia_minutos(entrada, salida, pausa='00:00'):
    """Presencia entre entrada y salida menos la pausa. Si la salida es anterior a la
    entrada, el turno acaba al día siguiente; si es la misma hora, es una jornada de 24 h
    (p. ej. una guardia de 07:00 a 07:00)."""
    duracion = (minutos(salida) - minutos(entrada)) % (24 * 60) or 24 * 60
    return duracion - minutos(pausa or '00:00')


def hndec(presencia_min):
    """Minutos de presencia -> 'HHMMSS' (formato de zparte.HNDEC)."""
    return f'{presencia_min // 60:02d}{presencia_min % 60:02d}00'


def minutos_de_hndec(valor):
    valor = (valor or '').strip()
    return int(valor[:2]) * 60 + int(valor[2:4]) if re.fullmatch(r'\d{6}', valor) else None


def _entero(valor):
    if valor in (None, ''):
        return 0
    if isinstance(valor, bool):
        raise ValueError
    if isinstance(valor, float) and not valor.is_integer():
        raise ValueError
    return int(valor)


def _texto(valor):
    texto = str(valor or '').strip()
    return texto or None


class ParteValidator:
    """Reglas del formulario de parte (ver README, sección del formulario)."""

    def __init__(self, hoy=None):
        self.hoy = hoy or date.today()

    def validar(self, datos, periodo=None, duplicado=False, presencia_guardada=None):
        """Devuelve un ParteValidado o lanza ErrorValidacion({campo: mensaje}).

        periodo: fila de zperiodos de la fecha (None si no existe).
        duplicado: ya hay otro parte del empleado ese día y turno.
        presencia_guardada: presencia (min) del parte que se edita, si no se reintroduce.
        """
        errores = {}
        datos = datos or {}

        # 1. Fecha y periodo de nómina
        fecha = None
        try:
            fecha = date.fromisoformat(str(datos.get('fecha') or ''))
        except ValueError:
            errores['fecha'] = 'Indica la fecha del parte (AAAA-MM-DD).'
        if fecha:
            if fecha > self.hoy:
                errores['fecha'] = 'No se pueden registrar partes de días futuros.'
            elif periodo is None:
                errores['fecha'] = 'No hay periodo de nómina para esa fecha.'
            elif periodo_traspasado(periodo):
                errores['fecha'] = 'El periodo de nómina de esa fecha ya está traspasado a nómina.'

        # 2. Turno
        turno = str(datos.get('turno') or '').strip().upper()
        if turno not in {clave for clave, _ in campos.TURNOS}:
            errores['turno'] = 'Elige un turno.'

        # 3. Duplicado (lo comprueba el servicio; aquí solo se informa)
        if duplicado and 'fecha' not in errores:
            errores['turno'] = 'Ya tienes un parte para ese día y turno.'

        tipodia = 'F' if datos.get('festivo_local') else (tipo_dia(fecha) if fecha else 'L')
        es_festivo = tipodia != 'L'

        # 4-7. Horas por bloque, motivo obligatorio y tramos festivos
        horas, motivos, total_he = {}, {}, 0
        entrada_horas = datos.get('horas') or {}
        entrada_motivos = datos.get('motivos') or {}
        for clave, titulo, sufijo, columna_motivo, cuenta in campos.BLOQUES:
            valores_bloque = entrada_horas.get(clave) or {}
            maximo = campos.MAX_HORAS_CASILLA if cuenta else campos.MAX_LLAMADAS_CASILLA
            suma_bloque = 0
            for tramo, etiqueta, festivo in campos.TRAMOS:
                ruta = f'horas.{clave}.{tramo}'
                try:
                    valor = _entero(valores_bloque.get(tramo))
                except (TypeError, ValueError):
                    errores[ruta] = 'Debe ser un número entero.'
                    continue
                if not 0 <= valor <= maximo:
                    errores[ruta] = f'Entre 0 y {maximo}.'
                    continue
                if valor and festivo and not es_festivo:
                    errores[ruta] = f'{etiqueta}: solo en sábado, domingo o festivo (marca "festivo local" si lo es).'
                horas[campos.columna(sufijo, tramo)] = valor
                suma_bloque += valor
            motivo = _texto(entrada_motivos.get(clave))
            if suma_bloque:
                if not motivo:
                    errores[f'motivos.{clave}'] = f'Indica el motivo de: {titulo.lower()}.'
                elif len(motivo) > campos.MAX_TEXTO:
                    errores[f'motivos.{clave}'] = f'Máximo {campos.MAX_TEXTO} caracteres.'
            motivos[columna_motivo] = motivo if suma_bloque else None
            if cuenta:
                total_he += suma_bloque

        if total_he > campos.MAX_TOTAL_HE:
            errores['total_he'] = f'El total de horas extra ({total_he} h) supera el máximo de {campos.MAX_TOTAL_HE} h.'

        # 8-9. Presencia
        entrada, salida = _texto(datos.get('entrada')), _texto(datos.get('salida'))
        pausa = _texto(datos.get('pausa')) or '00:00'
        presencia = presencia_guardada
        if entrada or salida:
            formato_ok = True
            for campo_hora, valor in (('entrada', entrada), ('salida', salida), ('pausa', pausa)):
                if not valor or not FORMATO_HORA.match(valor):
                    errores[campo_hora] = 'Formato HH:MM.'
                    formato_ok = False
            if formato_ok:
                presencia = presencia_minutos(entrada, salida, pausa)
                if presencia <= 0:
                    errores['presencia'] = 'La presencia debe ser mayor que cero (revisa entrada, salida y pausa).'
        if total_he:
            if presencia is None:
                errores.setdefault('presencia', 'Si hay horas extra, indica la hora de entrada y de salida.')
            elif presencia > 0 and total_he * 60 > presencia:
                # Si ya se pasa del máximo de 24 h, se mantiene ese mensaje (es el más claro)
                errores.setdefault('total_he', f'Las horas extra ({total_he} h) no pueden superar el tiempo de '
                                               f'presencia ({presencia // 60} h {presencia % 60:02d} min).')

        # 10. Situación del día (solo una)
        situacion = str(datos.get('situacion') or 'ninguna')
        if situacion not in {clave for clave, _, _ in campos.SITUACIONES}:
            errores['situacion'] = 'Elige solo una: Art. 21 descanso, Descanso o Teletrabajo.'

        # 11. Kilómetros
        km = None
        try:
            km = _entero(datos.get('km')) if datos.get('km') not in (None, '') else None
        except (TypeError, ValueError):
            errores['km'] = 'Debe ser un número entero.'
        if km is not None:
            if not 0 <= km <= campos.MAX_KM:
                errores['km'] = f'Entre 0 y {campos.MAX_KM}.'
            elif km and situacion == 'teletrabajo':
                errores['km'] = 'En teletrabajo no hay kilómetros de desplazamiento.'

        # 12. Marcas y sustitución
        marcas_validas = {c for c, _ in campos.MARCAS}
        marcas = set(datos.get('marcas') or [])
        if marcas - marcas_validas:
            errores['marcas'] = f'Marcas desconocidas: {", ".join(sorted(marcas - marcas_validas))}.'
        motivo_sustitucion = _texto(datos.get('motivo_sustitucion'))
        if campos.MARCA_SUSTITUCION in marcas:
            if not motivo_sustitucion:
                errores['motivo_sustitucion'] = 'Indica el motivo de la sustitución.'
            elif len(motivo_sustitucion) > campos.MAX_TEXTO:
                errores['motivo_sustitucion'] = f'Máximo {campos.MAX_TEXTO} caracteres.'
        else:
            motivo_sustitucion = None

        # 13. Observaciones
        observaciones = _texto(datos.get('observaciones'))
        if observaciones and len(observaciones) > campos.MAX_TEXTO:
            errores['observaciones'] = f'Máximo {campos.MAX_TEXTO} caracteres.'

        if errores:
            raise ErrorValidacion(errores)
        return ParteValidado(
            fecha=fecha, turno=turno, tipodia=tipodia, horas=horas, motivos=motivos, total_he=total_he,
            presencia_min=presencia, situacion=situacion, marcas=marcas & marcas_validas,
            motivo_sustitucion=motivo_sustitucion, km=km, observaciones=observaciones,
        )


class ParteService:
    """Partes del usuario autenticado (nunca de otro: el PERNR sale del token)."""

    def __init__(self, usuario, hoy=None):
        self.usuario = usuario
        self.hoy = hoy or date.today()
        self.validador = ParteValidator(self.hoy)

    # --- Consultas -------------------------------------------------------------------

    def _mio(self, mandt):
        parte = db.session.scalar(
            db.select(ZParte).where(ZParte.MANDT == mandt, ZParte.PERNR == self.usuario.pernr))
        if parte is None:
            raise ParteNoEncontrado('No existe ese parte.')
        return parte

    def listar(self, ejercicio):
        estados = {e.STATUS: e for e in db.session.scalars(db.select(EppartStatus)).all()}
        partes = db.session.scalars(
            db.select(ZParte).where(ZParte.PERNR == self.usuario.pernr, ZParte.EJERC == ejercicio)
            .order_by(ZParte.PADAT.desc(), ZParte.TURNO.asc())
        ).all()
        return {'ejercicio': ejercicio, 'partes': [self._resumen(p, estados.get(p.STAT)) for p in partes]}

    def obtener(self, mandt):
        return self._a_formulario(self._mio(mandt))

    # --- Escritura ---------------------------------------------------------------------

    def crear(self, datos):
        fecha = self._fecha(datos)
        validado = self.validador.validar(
            datos, periodo=periodo_de(fecha) if fecha else None,
            duplicado=self._duplicado(fecha, datos.get('turno')),
        )
        empleado = db.session.scalar(db.select(UserPayroll).where(UserPayroll.NUMPER == self.usuario.pernr))
        parte = ZParte(MANDT=self._nuevo_mandt(), PERNR=self.usuario.pernr, TIPO='T',
                       CRDAT=self.hoy, PERNRCR=self.usuario.pernr, USER_ID=self.usuario.pernr,
                       STAT=ESTADO_CREADO_POR_EMPLEADO)
        self._asignar(parte, validado, empleado)
        db.session.add(parte)
        db.session.commit()
        return self._a_formulario(parte)

    def actualizar(self, mandt, datos):
        parte = self._editable(mandt)
        fecha = self._fecha(datos)
        validado = self.validador.validar(
            datos, periodo=periodo_de(fecha) if fecha else None,
            duplicado=self._duplicado(fecha, datos.get('turno'), excluir=mandt),
            presencia_guardada=minutos_de_hndec(parte.HNDEC),
        )
        empleado = db.session.scalar(db.select(UserPayroll).where(UserPayroll.NUMPER == self.usuario.pernr))
        self._asignar(parte, validado, empleado)
        db.session.commit()
        return self._a_formulario(parte)

    def borrar(self, mandt):
        db.session.delete(self._editable(mandt))
        db.session.commit()

    # --- Auxiliares -----------------------------------------------------------------------

    def _editable(self, mandt):
        parte = self._mio(mandt)
        if parte.STAT != ESTADO_CREADO_POR_EMPLEADO:
            raise ConflictoParte('El parte ya tiene visto bueno o está validado: no se puede modificar.')
        return parte

    @staticmethod
    def _fecha(datos):
        try:
            return date.fromisoformat(str((datos or {}).get('fecha') or ''))
        except ValueError:
            return None

    def _duplicado(self, fecha, turno, excluir=None):
        if not fecha or not turno:
            return False
        consulta = db.select(ZParte.MANDT).where(
            ZParte.PERNR == self.usuario.pernr, ZParte.PADAT == fecha,
            ZParte.TIPO == 'T', ZParte.TURNO == str(turno).strip().upper())
        if excluir is not None:
            consulta = consulta.where(ZParte.MANDT != excluir)
        return db.session.scalar(consulta.limit(1)) is not None

    @staticmethod
    def _nuevo_mandt():
        mandt = int(time.time() * 1000)
        while db.session.scalar(db.select(ZParte.MANDT).where(ZParte.MANDT == mandt)) is not None:
            mandt += 1
        return mandt

    def _asignar(self, parte, v, empleado):
        periodo = periodo_de(v.fecha)
        parte.PADAT, parte.TURNO, parte.TIPODIA = v.fecha, v.turno, v.tipodia
        parte.MES, parte.EJERC = periodo.ID, periodo.EJERCICIO
        parte.REDAT = parte.UPDAT = self.hoy
        parte.CODGR = empleado.GRUPO if empleado else 0
        parte.DPTO = self._departamento(empleado)
        parte.CATEG = self._categoria(empleado)
        for columna, valor in v.horas.items():
            setattr(parte, columna, valor)
        for columna, motivo in v.motivos.items():
            setattr(parte, columna, motivo)
        if v.presencia_min is not None:
            parte.HN = v.presencia_min // 60
            parte.HNDEC = hndec(v.presencia_min)
        for clave, _, columna in campos.SITUACIONES:
            if columna:
                setattr(parte, columna, 't' if clave == v.situacion else 'f')
        for columna, _ in campos.MARCAS:
            setattr(parte, columna, campos.VALOR_MARCA if columna in v.marcas else None)
        parte.MOTIVOSUST = v.motivo_sustitucion
        parte.KM = v.km
        parte.OBSERV = v.observaciones

    @staticmethod
    def _departamento(empleado):
        if empleado is None or empleado.DEPARTMENT is None:
            return None
        departamento = db.session.get(DepartmentPayroll, empleado.DEPARTMENT)
        return departamento.NAME if departamento else None

    def _categoria(self, empleado):
        if empleado is not None and empleado.CLASSIFICATION_ID:
            clasificacion = db.session.get(TepClassificationPayroll, empleado.CLASSIFICATION_ID)
            if clasificacion:
                return clasificacion.CLASSIFICATION_SUMMARY
        return db.session.scalar(
            db.select(ZParte.CATEG).where(ZParte.PERNR == self.usuario.pernr, ZParte.CATEG.isnot(None))
            .order_by(ZParte.PADAT.desc()).limit(1))

    @staticmethod
    def _total_he(parte):
        return sum((getattr(parte, campos.columna(sufijo, tramo)) or 0)
                   for _, _, sufijo, _, cuenta in campos.BLOQUES if cuenta for tramo, _, _ in campos.TRAMOS)

    @staticmethod
    def _llamadas(parte):
        return sum((getattr(parte, f'LL{tramo}') or 0) for tramo, _, _ in campos.TRAMOS)

    def _resumen(self, parte, estado):
        presencia = minutos_de_hndec(parte.HNDEC)
        return {
            'mandt': parte.MANDT,
            'fecha': parte.PADAT.isoformat(),
            'turno': parte.TURNO,
            'tipodia': parte.TIPODIA,
            'estado': {'valor': parte.STAT, 'etiqueta': estado.DESCRIPTION if estado else parte.STAT,
                       'color': estado.COLOR if estado else None},
            'presencia': f'{presencia // 60}:{presencia % 60:02d}' if presencia is not None else None,
            'total_he': self._total_he(parte),
            'llamadas': self._llamadas(parte),
            'editable': parte.STAT == ESTADO_CREADO_POR_EMPLEADO,
        }

    def _a_formulario(self, parte):
        """Parte en el formato del formulario (para editarlo)."""
        presencia = minutos_de_hndec(parte.HNDEC)
        situacion = next((clave for clave, _, col in campos.SITUACIONES
                          if col and (getattr(parte, col) or '') == 't'), 'ninguna')
        return {
            'mandt': parte.MANDT,
            'fecha': parte.PADAT.isoformat(),
            'turno': parte.TURNO,
            'tipodia': parte.TIPODIA,
            'festivo_local': parte.TIPODIA == 'F' and tipo_dia(parte.PADAT) != 'F',
            'periodo': {'mes': parte.MES, 'ejercicio': parte.EJERC},
            'estado': parte.STAT,
            'editable': parte.STAT == ESTADO_CREADO_POR_EMPLEADO,
            'presencia_minutos': presencia,
            'horas': {
                clave: {tramo: getattr(parte, campos.columna(sufijo, tramo)) or 0 for tramo, _, _ in campos.TRAMOS}
                for clave, _, sufijo, _, _ in campos.BLOQUES
            },
            'motivos': {clave: getattr(parte, col) or '' for clave, _, _, col, _ in campos.BLOQUES},
            'total_he': self._total_he(parte),
            'situacion': situacion,
            'marcas': [c for c, _ in campos.MARCAS if (getattr(parte, c) or '').strip().upper() == campos.VALOR_MARCA],
            'motivo_sustitucion': parte.MOTIVOSUST or '',
            'km': parte.KM,
            'observaciones': parte.OBSERV or '',
        }
