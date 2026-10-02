# Contexto del proyecto

Proyecto final de Python (Tokio School, propuesta libre). Dashboard de RRHH:
- Backend: Flask + SQLAlchemy en `dashboard_rrhh/` (API REST bajo /api, Swagger en /api/doc)
- Frontend: Angular 22 + Tailwind en `frontend/`
- BD: MariaDB/MySQL `epartes_local` (esquema compartido con una app Java corporativa:
  userpayroll, zparte, zgrroles, zperiodos, eppartstatus, etc.). No renombrar
  tablas ni columnas existentes.

## Requisitos mínimos de la evaluación
BD, programación orientada a objetos, framework (Flask), login/control de accesos,
y documentación (memoria con requisitos funcionales y capturas, manual de instalación
desde cero). La entrega es un zip con la carpeta íntegra (sin node_modules, venv ni .env).

## Perfiles (RBAC), tomados de la tabla zgrroles (CODGR, PERNR, ROLNAME)
- ROLNAME = 'HR': RRHH, acceso total a todos los datos.
- ROLNAME = 'VB' o 'FI': mando. Solo ve los partes de los grupos (zparte.CODGR)
  donde tiene ese rol, más los suyos propios.
- Sin ninguna fila en zgrroles (o solo 'EM'): empleado normal. Solo ve sus propios
  partes (zparte.PERNR = userpayroll.NUMPER).
- Un usuario puede tener varios roles. Prioridad: HR > VB/FI > empleado. En el login
  elige el rol activo y el servidor DEBE verificar que lo posee.
- El filtrado de datos se aplica en el backend, nunca solo en el frontend.

## Reglas de trabajo
- Responde y comenta el código en español.
- Cambios pequeños y revisables; no toques lo que no se pida.
- Nunca guardes secretos en el repo; usa `.env` (ignorado) y `.env.example`.
- Antes de dar algo por terminado, ejecuta los tests y arranca la app para comprobarlo.
- Al acabar cada tarea, resume qué cambiaste y cómo probarlo.