# Claude Sessions Dashboard

Dashboard local para analizar tus sesiones de Claude Code: uso de agentes, tools
y skills, productividad por día y coste estimado. Lee los transcripts JSONL que
Claude Code guarda en `~/.claude/projects` — no envía nada a ningún sitio.

## Uso

```bash
cd claude-dashboard
pip install fastapi uvicorn   # o: uv add fastapi uvicorn
python3 server.py
# abre http://localhost:8020
```

## Qué muestra

- **KPIs**: sesiones, prompts, llamadas a tools, tokens, errores y coste estimado
  del rango elegido (7/30/90 días o todo).
- **Actividad diaria** y **productividad por día de la semana** (media de
  llamadas a tools por día activo).
- **Skills**: cuántas veces se ha invocado cada una y cuándo fue la última vez.
  Las skills instaladas (en `~/.claude/skills` y `.claude/skills` de cada
  proyecto) que nunca aparecen en los transcripts se marcan como candidatas a
  retirar — cada skill instalada ocupa contexto con su descripción aunque no se use.
- **Agentes**: invocaciones por `subagent_type`, fallos devueltos al orquestador
  (tool_result con `is_error`), errores internos dentro del transcript del
  subagente, tokens, llamadas a tools y duración media. La tasa de fallo es el
  indicador aproximado de qué agentes rinden peor.
- **Tools**: llamadas y tasa de error por tool; y una matriz de qué tools usa
  cada agente.
- **Modelos**: peticiones, tokens y coste estimado con tarifas de API por token
  (si usas suscripción, es orientativo — no es lo facturado).

## Probar con datos sintéticos

Si acabas de instalarlo o quieres ver el dashboard poblado:

```bash
python3 demo_data.py /tmp/claude-demo
CLAUDE_DASHBOARD_DIR=/tmp/claude-demo python3 server.py
```

`CLAUDE_DASHBOARD_DIR` apunta el analizador a otro directorio con la misma
estructura que `~/.claude`.

## Limitaciones conocidas

- El coste se estima a partir de `usage` de cada petición con precios por token
  publicados; el coste de caché se aproxima (lectura 0,1×, escritura 1,25×).
- La calidad de un agente se aproxima por su tasa de fallo y errores internos;
  no hay una medida semántica de "hizo bien la tarea".
- La asociación transcript-de-subagente ↔ tipo de agente se hace emparejando el
  prompt de la llamada `Task` con el primer mensaje del sidechain; si Claude Code
  cambia el formato podría degradarse a "(desconocido)".
- Los errores por tool se acumulan sobre todo el histórico (no por rango).
