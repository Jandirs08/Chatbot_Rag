"""
Script para analizar la mantenibilidad del código del chatbot RAG.
Evalúa calidad de código, complejidad, código muerto, dependencias,
documentación, modularidad y funciones duplicadas.
"""
import os
import sys
import subprocess
import re
import json
from pathlib import Path
import importlib.util
import ast
from collections import defaultdict
import datetime

# Directorio raíz del proyecto (ajustar si es necesario)
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_FILE = PROJECT_ROOT / "quality_report.txt"

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y devuelve su salida."""
    print(f"Ejecutando {descripcion}...")
    try:
        resultado = subprocess.run(
            comando, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return resultado.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar {descripcion}: {e}")
        return e.stdout if e.stdout else str(e)

def analizar_calidad_codigo():
    """Analiza la calidad del código usando Pylint y Flake8."""
    resultados = {}
    
    # Ejecutar Pylint
    try:
        pylint_output = ejecutar_comando(
            ["pylint", "--output-format=json", "backend"], 
            "Pylint"
        )
        try:
            pylint_json = json.loads(pylint_output)
            # Calcular puntuación promedio
            if pylint_json:
                scores = [msg.get('score', 0) for msg in pylint_json if 'score' in msg]
                avg_score = sum(scores) / len(scores) if scores else 0
                resultados["pylint_score"] = avg_score
                resultados["pylint_issues"] = len(pylint_json)
            else:
                resultados["pylint_score"] = 0
                resultados["pylint_issues"] = 0
        except json.JSONDecodeError:
            # Extraer puntuación usando regex si la salida no es JSON válido
            match = re.search(r"Your code has been rated at ([-\d.]+)/10", pylint_output)
            if match:
                resultados["pylint_score"] = float(match.group(1))
            else:
                resultados["pylint_score"] = 0
            resultados["pylint_issues"] = pylint_output.count(":")
    except Exception as e:
        resultados["pylint_error"] = str(e)
    
    # Ejecutar Flake8
    try:
        flake8_output = ejecutar_comando(
            ["flake8", "backend", "--count"], 
            "Flake8"
        )
        resultados["flake8_issues"] = int(flake8_output.strip()) if flake8_output.strip().isdigit() else len(flake8_output.splitlines())
    except Exception as e:
        resultados["flake8_error"] = str(e)
    
    return resultados

def analizar_complejidad_ciclomatica():
    """Analiza la complejidad ciclomática usando Radon."""
    resultados = {}
    
    # Ejecutar Radon para complejidad ciclomática
    try:
        cc_output = ejecutar_comando(
            ["radon", "cc", "backend", "--json"], 
            "Radon CC"
        )
        cc_data = json.loads(cc_output)
        
        # Analizar resultados
        total_funciones = 0
        funciones_complejas = 0
        complejidad_por_archivo = {}
        
        for archivo, funciones in cc_data.items():
            complejidad_archivo = []
            for funcion in funciones:
                total_funciones += 1
                if funcion["rank"] not in ["A", "B"]:
                    funciones_complejas += 1
                complejidad_archivo.append({
                    "nombre": funcion["name"],
                    "complejidad": funcion["complexity"],
                    "rango": funcion["rank"]
                })
            complejidad_por_archivo[archivo] = complejidad_archivo
        
        resultados["total_funciones"] = total_funciones
        resultados["funciones_complejas"] = funciones_complejas
        resultados["porcentaje_funciones_complejas"] = (funciones_complejas / total_funciones * 100) if total_funciones > 0 else 0
        resultados["detalle_por_archivo"] = complejidad_por_archivo
    except Exception as e:
        resultados["radon_error"] = str(e)
    
    return resultados

def analizar_codigo_muerto():
    """Identifica código muerto usando Vulture."""
    resultados = {}
    
    # Ejecutar Vulture
    try:
        vulture_output = ejecutar_comando(
            ["vulture", "backend"], 
            "Vulture"
        )
        
        # Analizar resultados
        lineas = vulture_output.splitlines()
        codigo_muerto = []
        
        for linea in lineas:
            if "% unused" in linea or "never used" in linea:
                codigo_muerto.append(linea.strip())
        
        resultados["codigo_muerto_encontrado"] = len(codigo_muerto)
        resultados["detalle_codigo_muerto"] = codigo_muerto
    except Exception as e:
        resultados["vulture_error"] = str(e)
    
    return resultados

def analizar_dependencias():
    """Analiza dependencias usando PyDep."""
    resultados = {}
    
    # Ejecutar PyDep (o alternativa)
    try:
        # PyDep no es tan común, podemos usar pipdeptree como alternativa
        pydep_output = ejecutar_comando(
            ["pipdeptree", "--json-tree"], 
            "Dependencias"
        )
        
        try:
            deps_data = json.loads(pydep_output)
            # Analizar dependencias
            todas_deps = set()
            deps_directas = set()
            
            for pkg in deps_data:
                deps_directas.add(pkg["package"]["key"])
                todas_deps.add(pkg["package"]["key"])
                for dep in pkg.get("dependencies", []):
                    todas_deps.add(dep["key"])
            
            resultados["total_dependencias"] = len(todas_deps)
            resultados["dependencias_directas"] = len(deps_directas)
            resultados["lista_dependencias_directas"] = sorted(list(deps_directas))
        except json.JSONDecodeError:
            resultados["error_formato"] = "No se pudo analizar la salida JSON de pipdeptree"
    except Exception as e:
        resultados["dependencias_error"] = str(e)
        
        # Alternativa: analizar requirements.txt si existe
        req_file = PROJECT_ROOT / "requirements.txt"
        if req_file.exists():
            with open(req_file, "r") as f:
                reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            resultados["total_dependencias_requirements"] = len(reqs)
            resultados["lista_dependencias_requirements"] = reqs
    
    return resultados

def analizar_documentacion():
    """Verifica que todas las funciones tengan docstrings."""
    resultados = {}
    
    # Ejecutar Pydocstyle
    try:
        pydoc_output = ejecutar_comando(
            ["pydocstyle", "backend"], 
            "Pydocstyle"
        )
        
        # Analizar resultados
        lineas = pydoc_output.splitlines()
        errores_doc = []
        
        for linea in lineas:
            if ":" in linea and "missing docstring" in linea.lower():
                errores_doc.append(linea.strip())
        
        resultados["errores_documentacion"] = len(errores_doc)
        resultados["detalle_errores"] = errores_doc
        
        # Análisis manual de docstrings
        total_funciones = 0
        funciones_sin_doc = 0
        
        for root, _, files in os.walk(PROJECT_ROOT / "backend"):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=file_path)
                            
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                                    total_funciones += 1
                                    if not ast.get_docstring(node):
                                        funciones_sin_doc += 1
                    except Exception as e:
                        print(f"Error al analizar {file_path}: {e}")
        
        resultados["total_funciones"] = total_funciones
        resultados["funciones_sin_docstring"] = funciones_sin_doc
        resultados["porcentaje_documentado"] = ((total_funciones - funciones_sin_doc) / total_funciones * 100) if total_funciones > 0 else 0
    except Exception as e:
        resultados["documentacion_error"] = str(e)
    
    return resultados

def analizar_modularidad():
    """Verifica la modularidad del código."""
    resultados = {}
    
    # Análisis de tamaño de archivos y responsabilidades
    archivos_grandes = []
    clases_grandes = []
    
    for root, _, files in os.walk(PROJECT_ROOT / "backend"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        contenido = f.read()
                        lineas = contenido.splitlines()
                        
                        # Verificar tamaño del archivo
                        if len(lineas) > 300:  # Umbral arbitrario para archivos grandes
                            archivos_grandes.append({
                                "archivo": file_path,
                                "lineas": len(lineas)
                            })
                        
                        # Analizar clases y métodos
                        tree = ast.parse(contenido, filename=file_path)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                metodos = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                                if len(metodos) > 15:  # Umbral arbitrario para clases grandes
                                    clases_grandes.append({
                                        "archivo": file_path,
                                        "clase": node.name,
                                        "metodos": len(metodos)
                                    })
                except Exception as e:
                    print(f"Error al analizar modularidad de {file_path}: {e}")
    
    resultados["archivos_grandes"] = archivos_grandes
    resultados["clases_grandes"] = clases_grandes
    
    return resultados

def detectar_funciones_duplicadas():
    """Detecta funciones que realizan tareas similares."""
    resultados = {}
    
    # Ejecutar herramienta para detectar código duplicado (por ejemplo, CPD de PMD)
    try:
        # Alternativa: usar una aproximación simple basada en hashes de funciones
        funciones_por_hash = defaultdict(list)
        
        for root, _, files in os.walk(PROJECT_ROOT / "backend"):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read(), filename=file_path)
                            
                            for node in ast.walk(tree):
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    # Crear un hash simple del cuerpo de la función
                                    # (esto es una aproximación, no detectará todas las duplicaciones)
                                    cuerpo = ast.unparse(node.body) if hasattr(ast, 'unparse') else str(node.body)
                                    hash_cuerpo = hash(cuerpo)
                                    funciones_por_hash[hash_cuerpo].append({
                                        "archivo": file_path,
                                        "funcion": node.name,
                                        "lineas": node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                                    })
                    except Exception as e:
                        print(f"Error al analizar duplicados en {file_path}: {e}")
        
        # Filtrar solo las funciones que aparecen más de una vez
        duplicados = {h: funcs for h, funcs in funciones_por_hash.items() if len(funcs) > 1}
        
        resultados["grupos_duplicados"] = len(duplicados)
        resultados["detalle_duplicados"] = list(duplicados.values())
    except Exception as e:
        resultados["duplicados_error"] = str(e)
    
    return resultados

def generar_informe(resultados):
    """Genera un informe detallado con los resultados del análisis."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"INFORME DE MANTENIBILIDAD - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Resumen ejecutivo
        f.write("RESUMEN EJECUTIVO\n")
        f.write("-" * 80 + "\n")
        
        # Calidad de código
        f.write("\n1. CALIDAD DE CÓDIGO\n")
        f.write("-" * 80 + "\n")
        
        if "pylint_score" in resultados["calidad"]:
            f.write(f"Puntuación Pylint: {resultados['calidad']['pylint_score']:.2f}/10\n")
        if "pylint_issues" in resultados["calidad"]:
            f.write(f"Problemas detectados por Pylint: {resultados['calidad']['pylint_issues']}\n")
        if "flake8_issues" in resultados["calidad"]:
            f.write(f"Problemas detectados por Flake8: {resultados['calidad']['flake8_issues']}\n")
        
        # Complejidad ciclomática
        f.write("\n2. COMPLEJIDAD CICLOMÁTICA\n")
        f.write("-" * 80 + "\n")
        
        if "total_funciones" in resultados["complejidad"]:
            f.write(f"Total de funciones analizadas: {resultados['complejidad']['total_funciones']}\n")
        if "funciones_complejas" in resultados["complejidad"]:
            f.write(f"Funciones con complejidad alta (C-F): {resultados['complejidad']['funciones_complejas']}\n")
        if "porcentaje_funciones_complejas" in resultados["complejidad"]:
            f.write(f"Porcentaje de funciones complejas: {resultados['complejidad']['porcentaje_funciones_complejas']:.2f}%\n")
        
        # Código muerto
        f.write("\n3. CÓDIGO MUERTO\n")
        f.write("-" * 80 + "\n")
        
        if "codigo_muerto_encontrado" in resultados["codigo_muerto"]:
            f.write(f"Elementos de código muerto detectados: {resultados['codigo_muerto']['codigo_muerto_encontrado']}\n")
            if resultados["codigo_muerto"]["codigo_muerto_encontrado"] > 0 and "detalle_codigo_muerto" in resultados["codigo_muerto"]:
                f.write("\nDetalle de código muerto:\n")
                for item in resultados["codigo_muerto"]["detalle_codigo_muerto"][:10]:  # Limitar a 10 para no sobrecargar el informe
                    f.write(f"- {item}\n")
                if len(resultados["codigo_muerto"]["detalle_codigo_muerto"]) > 10:
                    f.write(f"... y {len(resultados['codigo_muerto']['detalle_codigo_muerto']) - 10} más.\n")
        
        # Dependencias
        f.write("\n4. DEPENDENCIAS\n")
        f.write("-" * 80 + "\n")
        
        if "total_dependencias" in resultados["dependencias"]:
            f.write(f"Total de dependencias (directas e indirectas): {resultados['dependencias']['total_dependencias']}\n")
        if "dependencias_directas" in resultados["dependencias"]:
            f.write(f"Dependencias directas: {resultados['dependencias']['dependencias_directas']}\n")
        
        # Documentación
        f.write("\n5. DOCUMENTACIÓN\n")
        f.write("-" * 80 + "\n")
        
        if "total_funciones" in resultados["documentacion"]:
            f.write(f"Total de funciones/clases: {resultados['documentacion']['total_funciones']}\n")
        if "funciones_sin_docstring" in resultados["documentacion"]:
            f.write(f"Funciones/clases sin docstring: {resultados['documentacion']['funciones_sin_docstring']}\n")
        if "porcentaje_documentado" in resultados["documentacion"]:
            f.write(f"Porcentaje documentado: {resultados['documentacion']['porcentaje_documentado']:.2f}%\n")
        
        # Modularidad
        f.write("\n6. MODULARIDAD\n")
        f.write("-" * 80 + "\n")
        
        if "archivos_grandes" in resultados["modularidad"]:
            f.write(f"Archivos con más de 300 líneas: {len(resultados['modularidad']['archivos_grandes'])}\n")
            if resultados["modularidad"]["archivos_grandes"]:
                f.write("\nArchivos grandes:\n")
                for archivo in resultados["modularidad"]["archivos_grandes"][:5]:  # Limitar a 5
                    f.write(f"- {archivo['archivo']} ({archivo['lineas']} líneas)\n")
                if len(resultados["modularidad"]["archivos_grandes"]) > 5:
                    f.write(f"... y {len(resultados['modularidad']['archivos_grandes']) - 5} más.\n")
        
        if "clases_grandes" in resultados["modularidad"]:
            f.write(f"\nClases con más de 15 métodos: {len(resultados['modularidad']['clases_grandes'])}\n")
            if resultados["modularidad"]["clases_grandes"]:
                f.write("\nClases grandes:\n")
                for clase in resultados["modularidad"]["clases_grandes"][:5]:  # Limitar a 5
                    f.write(f"- {clase['clase']} en {clase['archivo']} ({clase['metodos']} métodos)\n")
                if len(resultados["modularidad"]["clases_grandes"]) > 5:
                    f.write(f"... y {len(resultados['modularidad']['clases_grandes']) - 5} más.\n")
        
        # Funciones duplicadas
        f.write("\n7. FUNCIONES DUPLICADAS\n")
        f.write("-" * 80 + "\n")
        
        if "grupos_duplicados" in resultados["duplicados"]:
            f.write(f"Grupos de funciones potencialmente duplicadas: {resultados['duplicados']['grupos_duplicados']}\n")
            if resultados["duplicados"]["grupos_duplicados"] > 0 and "detalle_duplicados" in resultados["duplicados"]:
                f.write("\nDetalle de duplicados (hasta 3 grupos):\n")
                for i, grupo in enumerate(resultados["duplicados"]["detalle_duplicados"][:3]):
                    f.write(f"\nGrupo {i+1}:\n")
                    for func in grupo:
                        f.write(f"- {func['funcion']} en {func['archivo']}\n")
                if len(resultados["duplicados"]["detalle_duplicados"]) > 3:
                    f.write(f"... y {len(resultados['duplicados']['detalle_duplicados']) - 3} grupos más.\n")
        
        # Recomendaciones
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMENDACIONES\n")
        f.write("=" * 80 + "\n\n")
        
        # Generar recomendaciones basadas en los resultados
        if "pylint_score" in resultados["calidad"] and resultados["calidad"]["pylint_score"] < 7.0:
            f.write("- Mejorar la calidad general del código siguiendo las recomendaciones de Pylint\n")
        
        if "porcentaje_funciones_complejas" in resultados["complejidad"] and resultados["complejidad"]["porcentaje_funciones_complejas"] > 20:
            f.write("- Reducir la complejidad ciclomática refactorizando las funciones más complejas\n")
        
        if "codigo_muerto_encontrado" in resultados["codigo_muerto"] and resultados["codigo_muerto"]["codigo_muerto_encontrado"] > 0:
            f.write("- Eliminar el código muerto detectado para mejorar la mantenibilidad\n")
        
        if "porcentaje_documentado" in resultados["documentacion"] and resultados["documentacion"]["porcentaje_documentado"] < 80:
            f.write("- Mejorar la documentación del código, especialmente en funciones públicas\n")
        
        if "archivos_grandes" in resultados["modularidad"] and resultados["modularidad"]["archivos_grandes"]:
            f.write("- Dividir los archivos grandes en módulos más pequeños y cohesivos\n")
        
        if "clases_grandes" in resultados["modularidad"] and resultados["modularidad"]["clases_grandes"]:
            f.write("- Refactorizar las clases grandes aplicando principios SOLID\n")
        
        if "grupos_duplicados" in resultados["duplicados"] and resultados["duplicados"]["grupos_duplicados"] > 0:
            f.write("- Eliminar duplicación de código extrayendo funciones comunes a módulos de utilidades\n")

def main():
    """Función principal que ejecuta todos los análisis de mantenibilidad."""
    print("Iniciando análisis de mantenibilidad del código...")
    
    resultados = {
        "calidad": analizar_calidad_codigo(),
        "complejidad": analizar_complejidad_ciclomatica(),
        "codigo_muerto": analizar_codigo_muerto(),
        "dependencias": analizar_dependencias(),
        "documentacion": analizar_documentacion(),
        "modularidad": analizar_modularidad(),
        "duplicados": detectar_funciones_duplicadas()
    }
    
    generar_informe(resultados)
    
    print(f"Análisis de mantenibilidad completado. Informe generado en {REPORT_FILE}")

if __name__ == "__main__":
    main()