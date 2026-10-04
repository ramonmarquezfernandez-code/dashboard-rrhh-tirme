# 🚀 Dashboard RRHH - Guía de Pruebas de API

## Descripción

Los endpoints de la API se prueban a mano con **Swagger UI** (documentación interactiva en `/api/doc`) o con **curl**. Las pruebas automáticas están en `tests/` y se ejecutan con `python -m pytest`.

---

## 🔐 Autenticación (obligatoria)

Todos los endpoints de datos (`/api/partes/*`) exigen un token JWT. Sin token responden `401`; con un perfil sin permiso, `403`. Los datos se filtran en el servidor según el perfil activo:

- **hr**: todo.
- **mando**: los grupos donde tiene rol VB/FI, más sus propios partes.
- **empleado**: solo sus partes.

Antes, crea los usuarios de prueba con `python seed.py`. La contraseña de todos es `Tirme2026!`; la lista está en el README.

**Endpoints de autenticación:**

- `POST /api/get-roles` con `{"email", "password"}` valida las credenciales y devuelve los perfiles del usuario. Si el correo o la contraseña no son válidos responde `401`, siempre con el mismo mensaje, para no revelar qué correos existen.
- `POST /api/login` con `{"email", "password", "rol"}` devuelve `{"token", "user"}`. `rol` es opcional; si no se indica, se usa el de mayor prioridad.
- `GET /api/me` devuelve los datos del token actual.

**Obtener un token con curl (bash):**

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "atorres@empresa.local", "password": "Tirme2026!", "rol": "hr"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['token'])")
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/partes
```

**En Swagger:** ejecuta `POST /api/login`, copia el `token`, pulsa **Authorize** y escribe `Bearer <token>`.

---

## 🟢 Swagger UI

### Características
- ✅ Documentación automática e interactiva
- ✅ Prueba endpoints directamente desde el navegador
- ✅ Genera especificación OpenAPI/Swagger
- ✅ Muestra esquemas de datos
- ✅ Mejor para desarrollo y testing

### Cómo Acceder

**1. Inicia el servidor:**
```bash
cd dashboard_rrhh
./run.sh
# o manualmente:
source venv/bin/activate
python app.py
```

**2. Abre en el navegador:**
```
http://localhost:5000/api/doc
```

### Endpoints disponibles en Swagger

La API tiene una única versión: todos sus endpoints aparecen en Swagger.

**Autenticación**

- `POST /api/get-roles`, `POST /api/login`, `GET /api/me`.

**Partes** (`/api/partes`)

| Endpoint | Perfiles | Uso |
|---|---|---|
| `GET /estados` | todos | Estados de parte (combos de filtro) |
| `GET /` | todos | Listado paginado (`page`, `per_page`) |
| `GET /empleado/{pernr}` | todos | Partes de un trabajador (404 si no es visible) |
| `GET /he-por-periodo` | todos | Pantalla *HE por periodos* |
| `GET /he-por-empleado` | todos | Pantalla *HE por empleado* |
| `GET /ranking-combo` | hr, mando | Pantalla *Ranking HE Combo* |
| `GET /sp-resumen-periodos` | todos | Pantalla *Total SP retribuidas* |
| `GET /plantilla-resumen` | hr, mando | Pantalla *Resumen General* (incluye `grupos` y `areas` para los combos) |
| `GET /personal` | hr, mando | Pantalla *Personal*: empleados activos (`grupo`, `direccion`); sin datos sensibles |
| `GET /ejercicios` | todos | Años con partes visibles más el año en curso, y el año por defecto (`actual`) |

**Partes del propio empleado** (`/api/mis-partes`, todos los perfiles; el número de personal sale siempre del token)

| Endpoint | Uso |
|---|---|
| `GET /configuracion` | Definición del formulario: bloques, tramos, situaciones, marcas, turnos, festivos y límites |
| `GET /?anio=2026` | Mis partes del ejercicio, con estado y si aún se pueden modificar |
| `POST /` | Crea un parte (estado `B`) |
| `GET /{mandt}` | Un parte propio en formato de formulario (404 si no es tuyo) |
| `PUT /{mandt}`, `DELETE /{mandt}` | Modifica o borra un parte propio en estado `B` (409 si ya tiene visto bueno) |

Ejemplo de alta y de error de validación:

```bash
curl -X POST http://localhost:5000/api/mis-partes -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fecha": "2026-10-02", "turno": "T", "entrada": "07:00", "salida": "18:00",
       "horas": {"normales": {"DL": 3}}, "motivos": {"normales": "Avería en planta"},
       "situacion": "ninguna", "marcas": ["SP"]}'
# 201 -> {"mandt": ..., "presencia_minutos": 660, "total_he": 3, "estado": "B", ...}

# Sin motivo o con más de 24 h extra -> 400:
# {"message": "Revisa los datos del parte.",
#  "errores": {"motivos.normales": "Indica el motivo de: horas extra normales."}}
```
| `GET /resumen-departamento`, `/resumen-trabajador`, `/comite`, `/he-anio-natural` | todos | Resúmenes del ejercicio (`anio`) |

**Parámetros comunes de las pantallas de HE:**

- `anio`: año de 4 cifras.
- `mes_desde`, `mes_hasta`: de 1 a 12.
- `anio_natural`: si es `true`, se filtra por la fecha del parte en lugar del mes de nómina.
- `periodo_id`: periodo de nómina de `zperiodos`.
- `departamento`, `pernr`, `estado`.

Si un parámetro no es válido, se responde `400` con `{"message"}`.

**Cálculos:** las fórmulas están en `services/horas_extra_service.py`.

- **Total HE en HE por periodo/empleado y en los resúmenes:** normales + compensar + busca + busca no pagada + combo (`TOTAL_HE_PERIODO`).
- **Total HE en el Ranking:** lo anterior, más las columnas F y las combo programadas (`TOTAL_HE_RANKING`).
- **HE compensables convertidas:** DL·1,6 + DF·2 + NL·2 + NF·2,5.

**SP:** un parte cuenta como SP si `zparte.SP` vale uno de `VALORES_MARCADO` (`'t'`, `'X'`, `'1'`, `'S'`), definido en `services/sp_service.py`. `'f'`, `'0'`, el valor vacío y NULL no cuentan. En los datos reales, revisados solo de forma estadística, SP marcado vale `'X'` y `'f'` significa "no marcado".

### Ventajas de Swagger
- Documentación clara con descripciones
- Modelos de datos visualizados
- Respuestas de ejemplo
- Parámetros autocompletados
- Sin necesidad de herramientas externas (Postman, etc.)

---

## 🛠️ Configuración

### Requerimientos
- Python 3.10+
- Flask 3.0.3
- Flask-RESTX 1.3.2 (automáticamente instalado)
- SQLAlchemy
- Marshmallow

### Instalación de Dependencias

Si aún no las has instalado:
```bash
cd dashboard_rrhh
source venv/bin/activate
pip install -r requirements.txt
```

### Variables de Entorno

Copia `.env.example` a `.env` y rellena tus valores (el `.env` no se sube al repositorio). Las variables son:
```env
FLASK_APP=app.py
FLASK_DEBUG=1
DB_USER=rrhh_user
DB_PASSWORD=<la misma que en el .env de la raíz>
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=epartes_local
SECRET_KEY=<clave aleatoria de 32 caracteres o más>
JWT_SECRET_KEY=<otra clave aleatoria>
TEST_DB_NAME=epartes_test
```

---

## 🔄 Endpoints Disponibles

### Base de URLs
- **API:** `http://localhost:5000/api/partes` (documentada en `http://localhost:5000/api/doc`)

### GET /api/partes
Obtiene listado paginado de partes.

**Parámetros:**
- `page` (int): Número de página (default: 1)
- `per_page` (int): Resultados por página (default: 20)

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/partes?page=1&per_page=20"
```

### GET /api/partes/empleado/{pernr}
Obtiene partes de un empleado específico.

**Parámetros:**
- `pernr` (string): Número de personal

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/partes/empleado/00000001"
```

### GET /api/partes/resumen-departamento
Obtiene resumen de horas extras por departamento.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/partes/resumen-departamento?anio=2026"
```

### GET /api/partes/resumen-trabajador
Obtiene resumen de horas extras por trabajador.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/partes/resumen-trabajador?anio=2026"
```

### GET /api/partes/comite
Obtiene resumen de horas extras para comité.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/partes/comite?anio=2026"
```

---

## 🚀 Iniciar Servidor

### Opción 1: Script automático
```bash
cd dashboard_rrhh
./run.sh
```

### Opción 2: Manual
```bash
cd dashboard_rrhh
source venv/bin/activate
python app.py
```

### Salida esperada:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

---

## ✅ Checklist de Verificación

- [ ] Servidor Flask ejecutándose en `http://localhost:5000`
- [ ] Swagger UI accesible en `http://localhost:5000/api/doc`
- [ ] `GET /api/partes` sin token devuelve 401 y con token devuelve los partes del perfil
- [ ] Endpoints responden con datos (o error de BD si no está conectada)
- [ ] Parámetros se aceptan correctamente
- [ ] Respuestas están en formato JSON

---

## 📝 Notas

- Si la BD no está conectada, verás errores de conexión, pero la API y las interfaces funcionan
- Swagger UI se genera automáticamente desde el código
- Ambas interfaces usan la misma API backend

---

## 🆘 Solución de Problemas

### "Connection refused" en localhost:5000
→ Asegúrate de que el servidor está corriendo: `./run.sh`

### "Module not found: flask_restx"
→ Instala las dependencias: `pip install -r requirements.txt`

### Swagger UI no carga
→ Recarga la página o limpia el caché del navegador

---

## 📚 Referencias

- Flask: https://flask.palletsprojects.com/
- Flask-RESTX: https://flask-restx.readthedocs.io/
- Swagger/OpenAPI: https://swagger.io/

---

**¡Listo para probar!** 🎉
