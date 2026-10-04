import { ChangeDetectorRef, Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { ConfiguracionParte, DatosParte, Parte, PartesService } from '../../services/partes.service';
import {
  fechaIso,
  formatoDuracion,
  presenciaMinutos,
  sumaBloque,
  tipoDia,
  totalHorasExtra,
  validarParte,
} from '../../services/parte-validacion';

const NOMBRES_TIPO_DIA: Record<string, string> = { L: 'Laborable', S: 'Sábado', D: 'Domingo', F: 'Festivo' };

// Formulario de parte de trabajo (alta y edición). Se construye a partir de la
// configuración del backend; las reglas se comprueban al momento en el navegador
// y el servidor las vuelve a validar al guardar.
@Component({
  selector: 'app-parte-formulario',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './parte-formulario.html',
})
export class ParteFormulario implements OnInit {
  private readonly partesService = inject(PartesService);
  private readonly router = inject(Router);
  private readonly ruta = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);

  public readonly hoy = fechaIso(new Date());
  public config = signal<ConfiguracionParte | null>(null);
  public formulario?: FormGroup;
  public mandt = signal<number | null>(null);
  public presenciaGuardada = signal<number | null>(null);
  public editable = signal(true);

  public erroresCliente = signal<Record<string, string>>({});
  public erroresServidor = signal<Record<string, string>>({});
  public mensajeServidor = signal('');
  public intentado = signal(false);
  public guardando = signal(false);
  public cargando = signal(true);

  public datos = signal<DatosParte | null>(null);
  public totalHe = computed(() => {
    const datos = this.datos();
    const config = this.config();
    return datos && config ? totalHorasExtra(datos, config) : 0;
  });
  public presencia = computed(() => {
    const datos = this.datos();
    if (!datos) {
      return null;
    }
    return datos.entrada || datos.salida
      ? presenciaMinutos(datos.entrada, datos.salida, datos.pausa)
      : this.presenciaGuardada();
  });
  public cruzaMedianoche = computed(() => {
    const datos = this.datos();
    return !!datos && /^\d\d:\d\d$/.test(datos.entrada) && /^\d\d:\d\d$/.test(datos.salida) && datos.salida <= datos.entrada;
  });
  public tipoDia = computed(() => {
    const datos = this.datos();
    const config = this.config();
    return datos && config ? tipoDia(datos.fecha, config.festivos, datos.festivo_local) : 'L';
  });
  public errores = computed(() => ({ ...this.erroresCliente(), ...this.erroresServidor() }));
  public listaErrores = computed(() => Object.values(this.errores()));

  public ngOnInit() {
    const mandt = Number(this.ruta.snapshot.paramMap.get('mandt')) || null;
    this.mandt.set(mandt);
    this.partesService.configuracion().subscribe({
      next: (config) => {
        this.config.set(config);
        this.formulario = this.crearFormulario(config);
        this.formulario.valueChanges
          .pipe(takeUntilDestroyed(this.destroyRef))
          .subscribe(() => this.recalcular());
        if (mandt) {
          this.cargarParte(mandt);
        } else {
          this.cargando.set(false);
          this.recalcular();
        }
      },
      error: () => this.fallo('No se ha podido cargar el formulario.'),
    });
  }

  private crearFormulario(config: ConfiguracionParte): FormGroup {
    const horas: Record<string, FormGroup> = {};
    const motivos: Record<string, FormControl<string>> = {};
    for (const bloque of config.bloques) {
      const tramos: Record<string, FormControl<number | null>> = {};
      for (const tramo of config.tramos) {
        tramos[tramo.clave] = new FormControl<number | null>(null);
      }
      horas[bloque.clave] = new FormGroup(tramos);
      motivos[bloque.clave] = this.fb.nonNullable.control('');
    }
    const marcas: Record<string, FormControl<boolean>> = {};
    for (const marca of config.marcas) {
      marcas[marca.clave] = this.fb.nonNullable.control(false);
    }
    return this.fb.group({
      fecha: this.fb.nonNullable.control(this.hoy),
      turno: this.fb.nonNullable.control(config.turnos[0]?.clave ?? 'M'),
      festivo_local: this.fb.nonNullable.control(false),
      entrada: this.fb.nonNullable.control(''),
      salida: this.fb.nonNullable.control(''),
      pausa: this.fb.nonNullable.control('00:00'),
      horas: new FormGroup(horas),
      motivos: new FormGroup(motivos),
      situacion: this.fb.nonNullable.control('ninguna'),
      marcas: new FormGroup(marcas),
      motivo_sustitucion: this.fb.nonNullable.control(''),
      km: new FormControl<number | null>(null),
      observaciones: this.fb.nonNullable.control(''),
    });
  }

  private cargarParte(mandt: number) {
    this.partesService.obtener(mandt).subscribe({
      next: (parte) => this.rellenar(parte),
      error: (error: HttpErrorResponse) =>
        this.fallo(error.status === 404 ? 'Ese parte no existe o no es tuyo.' : 'No se ha podido cargar el parte.'),
    });
  }

  private rellenar(parte: Parte) {
    const config = this.config()!;
    this.presenciaGuardada.set(parte.presencia_minutos);
    this.editable.set(parte.editable);
    this.formulario!.patchValue({
      fecha: parte.fecha,
      turno: parte.turno,
      festivo_local: parte.festivo_local,
      horas: parte.horas,
      motivos: parte.motivos,
      situacion: parte.situacion,
      marcas: Object.fromEntries(config.marcas.map((m) => [m.clave, parte.marcas.includes(m.clave)])),
      motivo_sustitucion: parte.motivo_sustitucion,
      km: parte.km,
      observaciones: parte.observaciones,
    });
    if (!parte.editable) {
      this.formulario!.disable({ emitEvent: false });
    }
    this.cargando.set(false);
    this.recalcular();
  }

  /** Datos del formulario en el formato que espera la API. */
  private leerDatos(): DatosParte {
    const valor = this.formulario!.getRawValue();
    return {
      ...valor,
      marcas: Object.entries(valor.marcas as Record<string, boolean>).filter(([, m]) => m).map(([c]) => c),
      km: valor.km === '' ? null : valor.km,
    };
  }

  private recalcular() {
    const config = this.config();
    if (!config || !this.formulario) {
      return;
    }
    const datos = this.leerDatos();
    this.datos.set(datos);
    this.actualizarTramosFestivos(datos, config);
    this.erroresCliente.set(validarParte(this.leerDatos(), config, this.hoy, this.presenciaGuardada()));
    this.erroresServidor.set({});
    this.changeDetector.markForCheck();
  }

  /** En día laborable las casillas festivas se vacían y se bloquean. */
  private actualizarTramosFestivos(datos: DatosParte, config: ConfiguracionParte) {
    if (!this.editable()) {
      return;
    }
    const laborable = tipoDia(datos.fecha, config.festivos, datos.festivo_local) === 'L';
    for (const bloque of config.bloques) {
      for (const tramo of config.tramos.filter((t) => t.festivo)) {
        const control = this.formulario!.get(['horas', bloque.clave, tramo.clave])!;
        if (laborable && control.enabled) {
          control.setValue(null, { emitEvent: false });
          control.disable({ emitEvent: false });
        } else if (!laborable && control.disabled) {
          control.enable({ emitEvent: false });
        }
      }
    }
  }

  // --- Ayudas para la plantilla ------------------------------------------------------

  public error(campo: string): string | null {
    const mensaje = this.errores()[campo];
    if (!mensaje) {
      return null;
    }
    const control = this.formulario?.get(campo.split('.'));
    const siempre = ['total_he', 'presencia'].includes(campo) || campo.startsWith('horas.');
    return this.intentado() || siempre || control?.dirty || this.erroresServidor()[campo] ? mensaje : null;
  }

  public subtotal(bloque: string): number {
    return sumaBloque(this.datos()?.horas[bloque]);
  }

  public situacionActual(): string {
    return this.datos()?.situacion ?? 'ninguna';
  }

  public marcada(clave: string): boolean {
    return !!this.datos()?.marcas.includes(clave);
  }

  public nombreTipoDia(): string {
    return NOMBRES_TIPO_DIA[this.tipoDia()] ?? this.tipoDia();
  }

  public duracion(minutos: number | null): string {
    return formatoDuracion(minutos);
  }

  public porcentajeTotal(): number {
    const maximo = this.config()?.limites.max_total_he ?? 24;
    return Math.min(100, (this.totalHe() / maximo) * 100);
  }

  // --- Guardar ---------------------------------------------------------------------------

  public guardar() {
    this.intentado.set(true);
    this.mensajeServidor.set('');
    if (!this.formulario || !this.editable() || Object.keys(this.erroresCliente()).length) {
      return;
    }
    this.guardando.set(true);
    const datos = this.leerDatos();
    const mandt = this.mandt();
    const peticion = mandt ? this.partesService.actualizar(mandt, datos) : this.partesService.crear(datos);
    peticion.subscribe({
      next: (parte) => {
        this.guardando.set(false);
        this.router.navigate(['/mis-partes'], {
          state: { mensaje: `Parte del ${parte.fecha} ${mandt ? 'actualizado' : 'guardado'} correctamente.` },
        });
      },
      error: (error: HttpErrorResponse) => {
        this.guardando.set(false);
        this.erroresServidor.set(error.error?.errores ?? {});
        this.mensajeServidor.set(error.error?.message ?? 'No se ha podido guardar el parte.');
        this.changeDetector.markForCheck();
      },
    });
  }

  private fallo(mensaje: string) {
    this.cargando.set(false);
    this.mensajeServidor.set(mensaje);
    this.changeDetector.markForCheck();
  }
}
