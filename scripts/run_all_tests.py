"""
Script para ejecutar todas las pruebas de forma secuencial usando Python.
Diseñado para ser compatible con Windows (cmd, PowerShell) y sistemas tipo Unix.
"""
import os
import sys
import subprocess
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

# Lista de scripts de prueba a ejecutar
TEST_SCRIPTS = [
    PROJECT_ROOT / "tests" / "test_mantenibilidad.py",
    PROJECT_ROOT / "tests" / "test_escalabilidad.py",
    PROJECT_ROOT / "tests" / "test_rendimiento.py",
    PROJECT_ROOT / "tests" / "test_integracion.py",
]

# Script para generar el informe unificado
REPORT_SCRIPT = PROJECT_ROOT / "scripts" / "generate_report.py"

def find_venv_python():
    """
    Encuentra la ruta al ejecutable de Python dentro del entorno virtual.
    Funciona tanto en Windows como en sistemas tipo Unix.
    """
    venv_dir = PROJECT_ROOT / "venvfinal1705"  # Cambiado a venvfinal1705
    if sys.platform == "win32":
        # Windows: venv/Scripts/python.exe
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        # Unix/Linux/macOS: venv/bin/python
        python_executable = venv_dir / "bin" / "python"

    if not python_executable.exists():
        print(f"Error: No se encontró el ejecutable de Python en el entorno virtual: {python_executable}")
        print("Asegúrate de haber creado y activado el entorno virtual.")
        return None
    return str(python_executable)

def ejecutar_script_python(python_exe: str, script_path: Path):
    """Ejecuta un script Python usando el intérprete del entorno virtual."""
    print(f"\n--- Ejecutando {script_path.name} ---")
    try:
        # Usamos check=True para lanzar una excepción si el comando falla
        subprocess.run(
            [python_exe, str(script_path)],
            check=True,
            cwd=PROJECT_ROOT, # Ejecutar desde la raíz del proyecto
            capture_output=True,
            text=True
        )
        print(f"{script_path.name} completado exitosamente.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar {script_path.name}:")
        print("--- STDOUT ---")
        print(e.stdout)
        print("--- STDERR ---")
        print(e.stderr)
        print(f"{script_path.name} falló.")
        return False
    except FileNotFoundError:
        print(f"Error: El script {script_path.name} no fue encontrado en {script_path}")
        return False
    except Exception as e:
        print(f"Error inesperado al ejecutar {script_path.name}: {e}")
        return False

def main():
    """Función principal para ejecutar todas las pruebas y generar el informe."""
    print("Iniciando ejecución de todas las pruebas...")

    python_exe = find_venv_python()
    if not python_exe:
        sys.exit(1)

    all_tests_successful = True

    # Ejecutar scripts de prueba
    for script in TEST_SCRIPTS:
        if not ejecutar_script_python(python_exe, script):
            all_tests_successful = False
            # Decide si quieres detenerte en el primer fallo o continuar
            # break # Descomenta para detenerte en el primer fallo
            pass # Comenta para detenerte en el primer fallo

    # Ejecutar script de generación de informe
    print("\n--- Generando informe unificado ---")
    if ejecutar_script_python(python_exe, REPORT_SCRIPT):
        print("Informe unificado generado exitosamente.")
    else:
        print("Hubo un error al generar el informe unificado.")
        all_tests_successful = False # Considerar el fallo del reporte como fallo general

    print("\nProceso de ejecución de pruebas completado.")
    if all_tests_successful:
        print("Todas las pruebas y la generación del informe se completaron sin errores reportados por los scripts.")
        sys.exit(0)
    else:
        print("Se detectaron errores durante la ejecución de las pruebas o la generación del informe.")
        sys.exit(1)

if __name__ == "__main__":
    main()