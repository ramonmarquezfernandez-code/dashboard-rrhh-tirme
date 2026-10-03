# Dashboard RRHH (Tirme)

Dashboard de Recursos Humanos para consultar partes de horas y horas extras.

| Pieza | Tecnología | Carpeta | URL en local |
|---|---|---|---|
| Base de datos | MariaDB 12.3 (Docker) | raíz (`docker-compose.yml`) | `127.0.0.1:3306` |
| Backend (API REST) | Python + Flask + SQLAlchemy | `dashboard_rrhh/` | http://localhost:5000 (Swagger en http://localhost:5000/api/doc) |
| Frontend | Angular 22 + Tailwind | `frontend/` | http://localhost:4200 |

La base de datos `epartes_local` se crea y se rellena sola con `epartes_local_backup.sql` la primera vez que se arranca el contenedor.

---

## 1. Requisitos previos

Instala lo siguiente y comprueba las versiones:

| Software | Versión | Comprobar con |
|---|---|---|
| Python | 3.10 o superior (probado con 3.13) | `python --version` (Windows) / `python3 --version` (Linux) |
| Node.js | 22.22+ o 24.15+ (lo exige Angular 22) | `node --version` |
| Docker + Docker Compose v2 | cualquier versión reciente | `docker compose version` |
| Git (opcional) | — | `git --version` |

**Windows:** instala [Python](https://www.python.org/downloads/) (marca *Add python.exe to PATH*), [Node.js LTS](https://nodejs.org/) y [Docker Desktop](https://www.docker.com/products/docker-desktop/). Docker Desktop debe estar abierto antes de seguir.

**Linux (Debian/Ubuntu):**

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
# Docker: https://docs.docker.com/engine/install/  (incluye el plugin "docker compose")
# Node.js 22/24: https://nodejs.org/en/download  (por ejemplo, con nvm)
```

> El puerto **3306** tiene que estar libre. Si ya tienes un MySQL/MariaDB local, páralo o cambia `DB_PORT` en los dos `.env` (paso 3).

---

## 2. Obtener el código

Descomprime el zip de la entrega o clona el repositorio y entra en la carpeta:

```bash
cd tirme-rrhh
```

Todos los comandos siguientes se ejecutan desde esa carpeta raíz, salvo que se indique lo contrario.

---

## 3. Crear los ficheros `.env`

Hay dos: uno para Docker (en la raíz) y otro para Flask (en `dashboard_rrhh/`). Copia las plantillas:

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
Copy-Item dashboard_rrhh\.env.example dashboard_rrhh\.env
```

**Linux:**

```bash
cp .env.example .env
cp dashboard_rrhh/.env.example dashboard_rrhh/.env
```

Edita los dos ficheros y pon tus propias contraseñas. **`DB_USER`, `DB_PASSWORD`, `DB_NAME` y `DB_PORT` deben coincidir en ambos.** En `dashboard_rrhh/.env` cambia también `SECRET_KEY`. `FLASK_DEBUG=1` activa el modo depuración (solo para desarrollo). Puedes generar la clave con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Los ficheros `.env` están en `.gitignore` y no se suben al repositorio.

---

## 4. Arrancar la base de datos

Igual en Windows y Linux (en Linux, antepón `sudo` si tu usuario no está en el grupo `docker`):

```bash
docker compose up -d
```

Espera a que el contenedor esté `healthy` (unos 10–20 segundos la primera vez):

```bash
docker compose ps
```

Comprueba que se cargaron los datos. Sustituye `rrhh_user` y `tu_password` por los valores de tu `.env`:

```bash
docker exec rrhh-mariadb mariadb -urrhh_user -ptu_password epartes_local -e "SHOW TABLES; SELECT COUNT(*) FROM zparte;"
```

Deben salir 9 tablas y 3 partes.

Al crear el contenedor también se crea una base de datos vacía, `epartes_test`, que usan los tests. Si tu volumen es anterior a ese cambio y no aparece al ejecutar `SHOW DATABASES;`, recréalo con `docker compose down -v` y luego `docker compose up -d`.

---

## 5. Backend (Flask)

**Windows (PowerShell):**

```powershell
cd dashboard_rrhh
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed.py
python -m pytest
python app.py
```

> Si PowerShell bloquea `Activate.ps1`, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo. En `cmd.exe`, actívalo con `venv\Scripts\activate.bat`.

**Linux:**

```bash
cd dashboard_rrhh
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python seed.py
python -m pytest
python app.py          # o bien: ./run.sh
```

- **`python seed.py`** crea los usuarios de prueba con contraseña cifrada (bcrypt) y sus roles (tabla de abajo). Se puede ejecutar varias veces.
- **`pytest`** debe terminar con `97 passed`.
  - Los tests de login, de acceso a datos y de cálculo de horas extra usan la BD `epartes_test` del contenedor.
  - Si MariaDB no está levantada, esos tests aparecen como *skipped*, con el motivo, y solo se ejecutan los 24 que no necesitan BD.
- **`python app.py`** deja el servidor escuchando en http://localhost:5000. Deja esa terminal abierta.

### Usuarios de prueba

Todos tienen la contraseña **`Tirme2026!`**.

| Email | Nº personal | Grupo | Roles (`zgrroles`) | Perfiles al entrar |
|---|---|---|---|---|
| atorres@empresa.local | 00000004 | 1 | HR | HR o empleado |
| mgarcia@empresa.local | 00000002 | 1 | VB del grupo 1 | mando o empleado |
| crodriguez@empresa.local | 00000003 | 2 | FI del grupo 2 | mando o empleado |
| jperez@empresa.local | 00000001 | 1 | — | empleado |
| eruiz@empresa.local | 00000005 | 2 | HR + VB del grupo 2 | HR, mando o empleado (para probar el selector) |

Qué ve cada perfil (el filtro se aplica en el backend):

- **HR**: todos los partes y toda la plantilla.
- **Mando** (VB/FI): los partes de los grupos donde tiene ese rol, más los suyos propios.
- **Empleado**: solo sus propios partes.

### Comprobación

Desde otra terminal:

- http://localhost:5000/ devuelve `{"status": "online", ...}`.
- http://localhost:5000/api/doc muestra Swagger. Para probar los endpoints protegidos:
  1. Ejecuta `POST /api/login` con `{"email": "atorres@empresa.local", "password": "Tirme2026!"}` y copia el `token`.
  2. Pulsa **Authorize** y escribe `Bearer <token>`.
- http://localhost:5000/api/partes sin token responde `401`.

---

## 6. Frontend (Angular)

En **otra terminal**, desde la carpeta raíz. Los comandos son iguales en Windows y Linux:

```bash
cd frontend
npm ci
npm start
```

Abre http://localhost:4200 y entra con uno de los [usuarios de prueba](#usuarios-de-prueba). El frontend llama a la API en `http://localhost:5000`, así que el backend del paso 5 tiene que estar en marcha.

- **Sesión:** se guarda en el navegador y se mantiene al recargar la página, durante 8 horas como máximo.
- **Menú lateral:** solo muestra las pantallas permitidas para el perfil con el que has entrado.

Para generar la versión de producción: `npm run build` (sale en `frontend/dist/`).

---

## 7. Operaciones habituales

| Acción | Comando |
|---|---|
| Parar la base de datos (conserva los datos) | `docker compose stop` |
| Volver a arrancarla | `docker compose start` |
| **Borrar la BD y recargar el dump desde cero** | `docker compose down -v`, luego `docker compose up -d` y después `python seed.py` |
| Volver a crear los usuarios de prueba | `python seed.py` (desde `dashboard_rrhh/` con el venv activo) |
| Ver logs de MariaDB | `docker compose logs -f mariadb` |
| Cargar datos desde CSV exportados (opcional) | `python cargar_csv.py <carpeta_con_csv>` (desde `dashboard_rrhh/` con el venv activo) |

---

## 8. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `docker compose up` falla con *port is already allocated* | El 3306 está ocupado. Para el otro servidor o cambia `DB_PORT` en los dos `.env`. |
| `docker compose up` dice *Define DB_PASSWORD en .env* | Falta el `.env` de la raíz (paso 3). |
| Flask: `Access denied for user` | Las credenciales de `dashboard_rrhh/.env` no coinciden con las del `.env` raíz. Si las cambiaste después del primer arranque, ejecuta `docker compose down -v` y `docker compose up -d`. |
| Flask: `Can't connect to MySQL server` | El contenedor no está levantado o aún no está `healthy` (`docker compose ps`). |
| `ModuleNotFoundError` al arrancar Flask | No está activado el venv o falta `pip install -r requirements.txt`. |
| Login: *Correo o contraseña incorrectos* con un usuario de prueba | Falta ejecutar `python seed.py`. El dump trae contraseñas sin cifrar, que ya no se aceptan. |
| `pytest` muestra tests *skipped* por *MariaDB de tests no disponible* | Levanta el contenedor. Si ya estaba levantado, falta la BD `epartes_test`: ejecuta `docker compose down -v` y luego `docker compose up -d`. |
| `./run.sh: Permission denied` (Linux) | `chmod +x run.sh` |
| Angular: *The Angular CLI requires a minimum Node.js version* | Actualiza Node a 22.22+ o 24.15+. |

---

## 9. Seguridad y limitaciones conocidas

### Medidas implementadas

| Medida | Dónde |
|---|---|
| Contraseñas guardadas como hash **bcrypt**; no se acepta ninguna en texto plano. | `services/auth_service.py` |
| Mismo mensaje y tiempo de respuesta tanto si el correo no existe como si la contraseña es errónea, para no revelar qué correos están registrados. `get-roles` también exige la contraseña. | `services/auth_service.py`, `routes/auth.py` |
| El servidor comprueba en `zgrroles` que el usuario tiene el perfil que elige al entrar (403 si no). | `routes/auth.py`, `services/rol_service.py` |
| Sesión con **JWT** firmado (HS256), válido 8 horas. | `config.py` |
| Todos los endpoints de datos exigen token (401) y perfil autorizado (403). | `@requiere_rol` en `services/acceso.py` |
| **Filtrado de datos en el backend**, en un único punto: HR sin filtro; mando, sus grupos más sus partes; empleado, solo los suyos. El frontend solo oculta menús. | `services/acceso.py` |
| Tests automáticos de aislamiento de datos para cada perfil. | `tests/test_acceso_datos.py` |
| CORS limitado a `http://localhost:4200`; Flask escucha solo en `127.0.0.1`; el modo debug se activa por `.env`. | `app.py` |
| Secretos fuera del repositorio (`.env` ignorado; solo se sube `.env.example`). | `.gitignore` |

### Limitaciones conocidas

| Limitación | Riesgo | Mejora posible |
|---|---|---|
| El token se guarda en `localStorage`. | Un ataque XSS podría leerlo. Angular escapa las plantillas por defecto, lo que reduce ese riesgo. | Cookie `httpOnly` + `SameSite` y protección CSRF. |
| Los roles y grupos van dentro del token. | Un cambio en `zgrroles` no se aplica hasta el siguiente login (como máximo 8 h). | Tokens más cortos con *refresh token*, o leer los roles en cada petición. |
| Cerrar sesión solo borra el token en el navegador. | Un token copiado sigue siendo válido hasta que caduca. | Lista de tokens revocados (*blocklist* de flask-jwt-extended). |
| No hay límite de intentos de login. | Ataques de fuerza bruta contra las contraseñas. | Limitar intentos por IP y usuario (p. ej. Flask-Limiter). |
| Si `SECRET_KEY` y `JWT_SECRET_KEY` no se definen en `.env`, se usa una clave por defecto, y la de `.env.example` es un texto de ejemplo. | Con una clave conocida, cualquiera podría fabricar tokens válidos. | Generar siempre claves propias (paso 3) o hacer que la app no arranque sin ellas. |
| Compatibilidad con la app Java corporativa, que comparte `userpayroll.PASSWORD`. | Python genera hashes `$2b$`. Spring Security (`BCryptPasswordEncoder` 5.2+) los acepta; versiones antiguas o jBCrypt solo aceptan `$2a$`. Python sí acepta los `$2a$` de Java. | Confirmarlo con la app corporativa antes de compartir la BD. |
| No se sabe qué valor marca un parte como SP (`zparte.SP` es `char(1)` y el dump no trae ejemplos). | Se acepta `'t'`, `'X'`, `'1'` o `'S'` (`VALORES_MARCADO` en `services/sp_service.py`); si la app corporativa usa otro valor, la pantalla de SP mostrará 0. | Confirmarlo con la app corporativa y ajustar la constante. |
| `python app.py` usa el servidor de desarrollo de Flask, sin HTTPS. | No apto para producción. | Servidor WSGI (waitress o gunicorn) detrás de un proxy con HTTPS. |

---

Más detalles de la API y ejemplos con Swagger y curl en [dashboard_rrhh/TESTING.md](dashboard_rrhh/TESTING.md).
