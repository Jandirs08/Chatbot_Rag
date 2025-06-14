# Gestión de Prompts del Bot

Este directorio contiene la lógica central para la gestión de prompts y personalidad del bot.

## Archivos Principales

### prompt.py

Este archivo centraliza la definición de la personalidad y los prompts del bot. Está diseñado para ser fácilmente modificable y extensible.

## Estructura del Código

### Constantes Principales

```python
BOT_NAME = "Asesor Virtual Académico"  # Nombre del bot
BOT_PERSONALITY = """..."""  # Personalidad base del bot
BASE_PROMPT_TEMPLATE = """..."""  # Plantilla base para prompts
```

### Funciones Disponibles

1. `get_asesor_academico_prompt(tools, tool_names, history, input_text, agent_scratchpad)`

   - Genera el prompt del asesor académico con todos los parámetros necesarios
   - Usa la personalidad base definida en `BOT_PERSONALITY`

2. `get_custom_prompt(nombre, tools, tool_names, history, input_text, agent_scratchpad)`
   - Genera un prompt personalizado con un nombre diferente
   - Mantiene la misma personalidad base pero permite cambiar el nombre

## Cómo Modificar

### 1. Cambiar el Nombre del Bot

```python
# Modificar la constante BOT_NAME
BOT_NAME = "Nuevo Nombre del Bot"
```

### 2. Modificar la Personalidad

La personalidad se define en `BOT_PERSONALITY` y tiene la siguiente estructura:

```python
BOT_PERSONALITY = """
Nombre: {nombre}
Rol: [Descripción del rol]

Rasgos de Personalidad:
- [Lista de rasgos]

Estilo Conversacional:
- [Lista de características del estilo]
"""
```

### 3. Modificar la Plantilla Base

La plantilla base (`BASE_PROMPT_TEMPLATE`) define la estructura general del prompt. Incluye:

- Introducción del bot
- Personalidad y estilo
- Herramientas disponibles
- Formato de pensamiento
- Estructura de la conversación

### 4. Agregar Nuevos Prompts

Para agregar un nuevo prompt:

1. Usar la función `get_custom_prompt()`:

```python
nuevo_prompt = get_custom_prompt(
    nombre="Nuevo Nombre",
    tools="...",
    tool_names="...",
    history="...",
    input_text="...",
    agent_scratchpad="..."
)
```

## Variables Requeridas

El template base requiere las siguientes variables:

- `nombre`: Nombre del bot
- `bot_personality`: Personalidad del bot
- `tools`: Descripción de herramientas disponibles
- `tool_names`: Lista de nombres de herramientas
- `history`: Historial de la conversación
- `input`: Entrada del usuario
- `agent_scratchpad`: Espacio de trabajo del agente

## Buenas Prácticas

1. **Mantener la Consistencia**: Al modificar la personalidad, asegúrate de mantener un tono y estilo consistentes.

2. **Documentación**: Documenta cualquier cambio significativo en la personalidad o estructura del prompt.

3. **Pruebas**: Después de modificar el prompt, prueba el bot para asegurar que mantiene el comportamiento deseado.

4. **Variables**: Asegúrate de que todas las variables requeridas estén disponibles cuando se use el prompt.

## Integración con ChainManager

El `ChainManager` utiliza este módulo para:

- Cargar la personalidad del bot
- Generar prompts con el contexto adecuado
- Mantener la consistencia en las respuestas

## Ejemplo de Uso

```python
from .prompt import get_asesor_academico_prompt

# Generar un prompt para el asesor académico
prompt = get_asesor_academico_prompt(
    tools="Herramientas disponibles...",
    tool_names="herramienta1, herramienta2",
    history="Historial de la conversación...",
    input_text="Pregunta del usuario",
    agent_scratchpad="..."
)
```
