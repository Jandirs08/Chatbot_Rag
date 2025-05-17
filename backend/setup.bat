@echo off
echo Configurando entorno de desarrollo...

REM Ruta del entorno virtual (fuera de backend)
set VENV_DIR=..\venv3100

REM Crear entorno virtual si no existe
if not exist %VENV_DIR% (
    echo Creando entorno virtual con Python 3.10...
    py -3.10 -m venv %VENV_DIR%
)

REM Activar entorno virtual
echo Activando entorno virtual...
call %VENV_DIR%\Scripts\activate.bat

REM Verificar si el entorno está activado
if "%VIRTUAL_ENV%"=="" (
    echo Error: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

REM Actualizar pip
echo Actualizando pip...
python -m pip install --upgrade pip

REM Cambiar el directorio a backend para instalar dependencias
cd /d "%~dp0"

REM Instalar dependencias desde el archivo requirements.txt
echo Instalando dependencias...
pip install -r requirements.txt

REM Verificar instalación de paquetes
echo Verificando instalación...
python -c "import redis; print('Redis instalado correctamente')"
python -c "import langchain; print('LangChain instalado correctamente')"
python -c "import chromadb; print('ChromaDB instalado correctamente')"
python -c "import spacy; print('spaCy instalado correctamente')"

echo ¡Instalación completada!
pause
