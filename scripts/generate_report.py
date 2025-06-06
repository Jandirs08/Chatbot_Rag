"""
Script para generar un informe unificado con los resultados de todas las pruebas.
Combina los informes individuales en un único documento.
"""
import json
from pathlib import Path
from datetime import datetime

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
UNIFIED_REPORT = REPORTS_DIR / "unified_test_report.txt"

# Archivos de informe individuales
REPORT_FILES = {
    "mantenibilidad": PROJECT_ROOT / "maintainability_report.txt",
    "escalabilidad": PROJECT_ROOT / "scalability_report.txt",
    "rendimiento": PROJECT_ROOT / "performance_report.txt",
    "integracion": PROJECT_ROOT / "integration_report.txt"
}

def leer_informe(ruta: Path) -> str:
    """Lee el contenido de un archivo de informe."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Informe no encontrado: {ruta}"
    except Exception as e:
        return f"Error al leer el informe {ruta}: {str(e)}"

def generar_informe_unificado():
    """Genera un informe unificado combinando todos los informes individuales."""
    # Asegurar que el directorio de informes existe
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(UNIFIED_REPORT, "w", encoding="utf-8") as f:
        # Encabezado
        f.write("=" * 80 + "\n")
        f.write(f"INFORME UNIFICADO DE PRUEBAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Resumen ejecutivo
        f.write("RESUMEN EJECUTIVO\n")
        f.write("-" * 80 + "\n")
        f.write("Este informe combina los resultados de todas las pruebas realizadas:\n")
        f.write("- Pruebas de Mantenibilidad\n")
        f.write("- Pruebas de Escalabilidad\n")
        f.write("- Pruebas de Rendimiento\n")
        f.write("- Pruebas de Integración\n\n")
        
        # Informes individuales
        for nombre, ruta in REPORT_FILES.items():
            f.write("=" * 80 + "\n")
            f.write(f"INFORME DE {nombre.upper()}\n")
            f.write("=" * 80 + "\n\n")
            
            contenido = leer_informe(ruta)
            f.write(contenido)
            f.write("\n\n")
        
        # Recomendaciones generales
        f.write("=" * 80 + "\n")
        f.write("RECOMENDACIONES GENERALES\n")
        f.write("=" * 80 + "\n\n")
        f.write("1. Revisar y corregir los errores identificados en cada sección\n")
        f.write("2. Implementar pruebas automatizadas en el pipeline de CI/CD\n")
        f.write("3. Establecer métricas de rendimiento y escalabilidad\n")
        f.write("4. Documentar los procedimientos de prueba\n")
        f.write("5. Realizar pruebas periódicas para mantener la calidad\n")

def main():
    """Función principal para generar el informe unificado."""
    print("Generando informe unificado de pruebas...")
    generar_informe_unificado()
    print(f"Informe unificado generado en: {UNIFIED_REPORT}")

if __name__ == "__main__":
    main() 