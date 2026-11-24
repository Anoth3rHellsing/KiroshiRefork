# KiroshiRefork

El proyecto original (**Kiroshi Documentation System**, una app de Streamlit para documentar casos de soporte IT) está archivado y su código se eliminó de la rama principal.

Nada se ha perdido: todo sigue en el historial de git. El último commit con el proyecto completo es `f3eb50d`. Para recuperarlo:

```bash
git checkout f3eb50d        # ver el proyecto tal como estaba
git checkout f3eb50d -- .   # o restaurar sus archivos en la rama actual
```

---

## Siguiente paso: aprender sobre ahorro de tokens

Este repo queda como espacio para investigar técnicas de ahorro de tokens en aplicaciones con LLMs. Estas son las palancas principales, ordenadas de más barata a más costosa en calidad:

### 1. Medir antes de optimizar
- Contar tokens antes de enviar (`messages.count_tokens` en la API de Claude).
- Leer `usage` en cada respuesta: `input_tokens`, `output_tokens`, `cache_read_input_tokens` y `cache_creation_input_tokens`.
- Medir el **coste por tarea completada**, no por petición. Una petición más barata que necesita reintentos no ahorra nada.

### 2. Prompt caching (la mayor ganancia, y sin perder calidad)
- La caché funciona por **coincidencia de prefijo**: cualquier byte que cambie invalida todo lo que viene después.
- Orden: lo estable primero (system prompt fijo, lista de herramientas determinista) y lo variable al final (la pregunta, timestamps, IDs).
- Leer de caché cuesta ~0,1× del precio normal y escribir ~1,25×.
- Invalidadores silenciosos típicos: `datetime.now()` en el system prompt, JSON sin ordenar, herramientas que cambian entre peticiones.

### 3. Higiene del contexto en conversaciones largas
- **Recortar historial**: no reenviar todo si no hace falta.
- **Context editing**: borrar resultados de herramientas antiguos.
- **Compaction**: resumir automáticamente el contexto viejo al acercarse al límite.
- **RAG / recuperación**: buscar los fragmentos relevantes en vez de meter documentos enteros en el prompt.

### 4. Ahorro en la salida
- Pedir respuestas concisas en el prompt y usar formatos estructurados (JSON con esquema).
- Ajustar el nivel de `effort` según la tarea: bajo para tareas simples, alto para tareas difíciles.

### 5. Procesamiento por lotes
- La Batch API cuesta un 50 % menos si la latencia no importa.

### 6. Elegir el modelo (aquí sí hay compromiso de calidad)
- Modelos pequeños para clasificación y extracción, grandes para razonamiento.
- Ojo: cada modelo tiene su propia caché, así que una cascada de modelos pierde la reutilización de caché.

---

## Ejercicio con el proyecto antiguo

`kiroshi_chat.py` (en el commit `f3eb50d`) enviaba en cada mensaje un system prompt de ~7.800 caracteres (≈2.000 tokens) más todo el historial guardado en `kiroshi_memory.json`. Es un buen caso de estudio:

1. Medir cuántos tokens se gastaban por turno.
2. Separar la parte fija del prompt de la variable para que se pueda cachear.
3. Limitar o resumir el historial en lugar de reenviarlo entero.

## Documentación útil
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Token counting: https://platform.claude.com/docs/en/build-with-claude/token-counting
- Context editing: https://platform.claude.com/docs/en/build-with-claude/context-editing
- Compaction: https://platform.claude.com/docs/en/build-with-claude/compaction
- Batch API: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Optimizar coste e inteligencia: https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
