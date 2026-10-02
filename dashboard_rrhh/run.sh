#!/bin/bash

# Script para iniciar el servidor Flask del Dashboard RRHH

echo "🚀 Iniciando servidor Dashboard RRHH..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navegar al directorio del proyecto
cd "$(dirname "$0")"

# Activar el entorno virtual
source venv/bin/activate

# Mostrar información del servidor
echo "📋 Información del Servidor:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏠 Inicio:              http://localhost:5000"
echo "📚 Swagger UI:          http://localhost:5000/api/doc"
echo "🧪 Cliente Pruebas:     $(pwd)/client.html"
echo "📡 API v1:              http://localhost:5000/api/partes"
echo "📡 API v2 (con Swagger):http://localhost:5000/api/v2/partes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏱️  El servidor se iniciará en unos momentos..."
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Ejecutar la aplicación
python app.py
