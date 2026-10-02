# 🚀 Dashboard RRHH - Guía de Pruebas de API

## Descripción

Se han creado **dos interfaces** para probar los endpoints de la API:

1. **Swagger UI (Documentación Interactiva)** ✨ - Recomendado
2. **Cliente HTML Simple** 🧪 - Para pruebas rápidas

---

## 🟢 Opción 1: Swagger UI (Recomendado)

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

### Endpoints Disponibles en Swagger (API v2)

- `GET /api/v2/partes` - Listado paginado de partes
- `GET /api/v2/partes/empleado/{pernr}` - Partes de un empleado
- `GET /api/v2/partes/resumen-departamento` - Resumen por departamento
- `GET /api/v2/partes/resumen-trabajador` - Resumen por trabajador
- `GET /api/v2/partes/comite` - Horas extras para comité

### Ventajas de Swagger
- Documentación clara con descripciones
- Modelos de datos visualizados
- Respuestas de ejemplo
- Parámetros autocompletados
- Sin necesidad de herramientas externas (Postman, etc.)

---

## 🟡 Opción 2: Cliente HTML Simple

### Características
- ✅ Interfaz visual amigable
- ✅ Formularios para cada endpoint
- ✅ Resultados en tiempo real
- ✅ No requiere instalación adicional
- ✅ Bueno para pruebas rápidas

### Cómo Acceder

**1. Inicia el servidor (igual que Swagger):**
```bash
cd dashboard_rrhh
./run.sh
```

**2. Abre el archivo HTML:**
```bash
# Opción A: Abrir directamente
open client.html

# Opción B: Desde el navegador
file:///home/ramonmf/Documentos/Proyecto_Fin/App/Python/dashboard_rrhh/client.html
```

### Interfaz del Cliente
- 6 tarjetas interactivas, una por cada endpoint
- Campos de entrada personalizables
- Respuestas formateadas en JSON
- Indicadores de éxito/error
- Configuración de URL base

### Endpoints Disponibles en Cliente (API v1)

- `GET /api/partes?page=1&per_page=20` - Listado paginado
- `GET /api/partes/empleado/{pernr}` - Partes de empleado
- `GET /api/partes/resumen-departamento?anio=2026` - Resumen departamento
- `GET /api/partes/resumen-trabajador?anio=2026` - Resumen trabajador
- `GET /api/partes/comite?anio=2026` - Horas extras comité

---

## 📊 Comparativa

| Característica | Swagger UI | Cliente HTML |
|---|---|---|
| Documentación automática | ✅ | ❌ |
| Visualización de esquemas | ✅ | ❌ |
| Interfaz visual | ✅ | ✅ |
| Pruebas rápidas | ✅ | ✅ |
| Curl ejemplos | ✅ | ❌ |
| Validación de parámetros | ✅ | ✅ |
| Recomendado para | Desarrollo | Testing rápido |

---

## 🛠️ Configuración

### Requerimientos
- Python 3.8+
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
pip install flask-restx
```

### Variables de Entorno

Verifica que `.env` tenga la configuración correcta:
```env
FLASK_APP=app.py
FLASK_ENV=development
DB_USER=rrhh_user
DB_PASSWORD=1234567890
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=epartes_local
SECRET_KEY=clave_secreta_desarrollo_rrhh
```

---

## 🔄 Endpoints Disponibles

### Base de URLs
- **API v1 (Legacy):** `http://localhost:5000/api/partes`
- **API v2 (Swagger):** `http://localhost:5000/api/v2/partes`

### GET /api/partes
Obtiene listado paginado de partes.

**Parámetros:**
- `page` (int): Número de página (default: 1)
- `per_page` (int): Resultados por página (default: 20)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/partes?page=1&per_page=20"
```

### GET /api/partes/empleado/{pernr}
Obtiene partes de un empleado específico.

**Parámetros:**
- `pernr` (string): Número de personal

**Ejemplo:**
```bash
curl "http://localhost:5000/api/partes/empleado/00000001"
```

### GET /api/partes/resumen-departamento
Obtiene resumen de horas extras por departamento.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/partes/resumen-departamento?anio=2026"
```

### GET /api/partes/resumen-trabajador
Obtiene resumen de horas extras por trabajador.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/partes/resumen-trabajador?anio=2026"
```

### GET /api/partes/comite
Obtiene resumen de horas extras para comité.

**Parámetros:**
- `anio` (string): Año de ejercicio (default: 2026)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/partes/comite?anio=2026"
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
- [ ] Cliente HTML funciona en `file:///.../client.html`
- [ ] Endpoints responden con datos (o error de BD si no está conectada)
- [ ] Parámetros se aceptan correctamente
- [ ] Respuestas están en formato JSON

---

## 📝 Notas

- Si la BD no está conectada, verás errores de conexión, pero la API y las interfaces funcionan
- Swagger UI se genera automáticamente desde el código
- El cliente HTML es totalmente independiente y funciona sin BD
- Ambas interfaces usan la misma API backend

---

## 🆘 Solución de Problemas

### "Connection refused" en localhost:5000
→ Asegúrate de que el servidor está corriendo: `./run.sh`

### "Module not found: flask_restx"
→ Instala la dependencia: `pip install flask-restx`

### Cliente HTML no muestra respuestas
→ Verifica que la URL base sea correcta: `http://localhost:5000`

### Swagger UI no carga
→ Recarga la página o limpia el caché del navegador

---

## 📚 Referencias

- Flask: https://flask.palletsprojects.com/
- Flask-RESTX: https://flask-restx.readthedocs.io/
- Swagger/OpenAPI: https://swagger.io/

---

**¡Listo para probar!** 🎉
