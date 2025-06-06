"""
Script para instalar todas las dependencias necesarias del proyecto.
Crea un entorno virtual con Python 3.10 e instala los paquetes requeridos.
"""
import os
import sys
import subprocess
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
VENV_NAME = "venvfinal1705"

# Lista de dependencias necesarias
DEPENDENCIES = [
    "psutil",           # Para monitoreo de recursos
    "requests",         # Para peticiones HTTP
    "matplotlib",       # Para gráficos
    "aiohttp",         # Para peticiones HTTP asíncronas
    "pytest",          # Para pruebas
    "pytest-asyncio",  # Para pruebas asíncronas
    "black",           # Para formateo de código
    "flake8",          # Para linting
    "mypy",            # Para verificación de tipos
    "python-dotenv",   # Para variables de entorno
]

def ejecutar_comando(comando: str, shell: bool = True) -> bool:
    """Ejecuta un comando y retorna True si fue exitoso."""
    try:
        # Usar subprocess.run con capture_output para capturar la salida
        resultado = subprocess.run(comando, shell=shell, check=True, capture_output=True, text=True)
        print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar comando: {comando}")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Salida: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def crear_entorno_virtual():
    """Crea un nuevo entorno virtual con Python 3.10."""
    print(f"Creando entorno virtual '{VENV_NAME}' con Python 3.10...")
    
    # Eliminar entorno virtual existente si existe
    venv_path = PROJECT_ROOT / VENV_NAME
    if venv_path.exists():
        print(f"Eliminando entorno virtual existente '{VENV_NAME}'...")
        if sys.platform == "win32":
            ejecutar_comando(f"rmdir /s /q {venv_path}")
        else:
            ejecutar_comando(f"rm -rf {venv_path}")
    
    # Crear nuevo entorno virtual
    if sys.platform == "win32":
        if not ejecutar_comando("py -3.10 -m venv venvfinal1705"):
            print("Error: No se pudo crear el entorno virtual. Asegúrate de tener Python 3.10 instalado.")
            return False
    else:
        if not ejecutar_comando("python3.10 -m venv venvfinal1705"):
            print("Error: No se pudo crear el entorno virtual. Asegúrate de tener Python 3.10 instalado.")
            return False
    
    return True

def instalar_dependencias():
    """Instala todas las dependencias en el entorno virtual."""
    print("Instalando dependencias...")
    
    # Activar entorno virtual e instalar dependencias
    if sys.platform == "win32":
        pip_cmd = f"{VENV_NAME}\\Scripts\\python.exe -m pip"
    else:
        pip_cmd = f"{VENV_NAME}/bin/python -m pip"
    
    # Instalar dependencias
    for dep in DEPENDENCIES:
        print(f"Instalando {dep}...")
        if not ejecutar_comando(f"{pip_cmd} install {dep}"):
            print(f"Error al instalar {dep}")
            return False
    
    return True

def main():
    """Función principal para instalar todas las dependencias."""
    print("Iniciando instalación de dependencias...")
    
    # Crear entorno virtual
    if not crear_entorno_virtual():
        sys.exit(1)
    
    # Instalar dependencias
    if not instalar_dependencias():
        print("Error: No se pudieron instalar todas las dependencias.")
        sys.exit(1)
    
    print("\nInstalación completada exitosamente!")
    print("\nPara activar el entorno virtual:")
    if sys.platform == "win32":
        print(f"    .\\{VENV_NAME}\\Scripts\\activate.bat")
    else:
        print(f"    source {VENV_NAME}/bin/activate")
    
    print("\nPara ejecutar los tests:")
    print("    python scripts/run_all_tests.py")

if __name__ == "__main__":
    main() 