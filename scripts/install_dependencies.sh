#!/bin/bash
# Script para instalar todas las dependencias necesarias para las pruebas
# Autor: Usuario
# Fecha: 2023

echo "Instalando dependencias para pruebas de chatbot RAG..."

# Verificar si pip está instalado
if ! command -v pip &> /dev/null; then
    echo "Error: pip no está instalado. Por favor, instala Python y pip primero."
    exit 1
fi

# Crear entorno virtual (opcional pero recomendado)
echo "Creando entorno virtual..."
python -m venv venv

# Activar entorno virtual
if [ -d "venv/Scripts" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Instalar dependencias principales del proyecto
echo "Instalando dependencias del proyecto..."
pip install -r requirements.txt

# Instalar herramientas para pruebas de mantenibilidad
echo "Instalando herramientas para pruebas de mantenibilidad..."
pip install pylint flake8 radon vulture pipdeptree pydocstyle

# Instalar herramientas para pruebas de escalabilidad
echo "Instalando herramientas para pruebas de escalabilidad..."
pip install locust psutil matplotlib

# Instalar herramientas para pruebas de rendimiento
echo "Instalando herramientas para pruebas de rendimiento..."
pip install cProfile

# Instalar herramientas para pruebas de integración
echo "Instalando herramientas para pruebas de integración..."
pip install pytest pytest-asyncio python-dot