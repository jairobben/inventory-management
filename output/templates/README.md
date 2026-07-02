# Plantillas adaptadas — harness de orquestador único + sub-agentes efímeros (GSD)

Origen: `docs/en/resources/templates/` y `skills/harness-creator/` del curso
[walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering),
adaptadas a un harness con **un orquestador y sub-agentes efímeros** sobre GSD
(fork `open-gsd/get-shit-done-redux`), para un repo Python (API) + React
(frontend) desplegado en Cloud Run/GCP.

## Principio de adaptación

GSD ya aporta la capa de planificación (`.planning/`, `STATE.md`, `CONTEXT.md`,
`PLAN-*.md`, `VERIFICATION.md`, bucle Discuss → Plan → Execute → Verify →
Ship). Estas plantillas **no la duplican**: cubren lo que el curso añade y GSD
no trae de serie — evidencia de verificación por sesión, scope machine-readable,
checklist de estado limpio, rúbrica de evaluación calibrable y briefs
autocontenidos para los sub-agentes.

## Ficheros

| Fichero | Origen en el curso | Adaptación principal |
|---|---|---|
| `AGENTS.md` | `resources/templates/AGENTS.md` + plantilla interna de la skill | Reglas de orquestador (nunca edita código; delega y sintetiza), startup que lee `.planning/STATE.md`, verificación de dos stacks, DoD que exige `VERIFICATION.md` |
| `init.sh` | `resources/templates/init.sh` | De un solo stack npm a backend Python (pytest/ruff, exit-5 tolerado) + frontend React (lint/test/build) + dry-run opcional de deploy (nunca muta cloud) |
| `feature_list.json` | `resources/templates/feature_list.json` | Campos nuevos: `phase` (enlace al plan GSD), `assigned_subagent`, `dependencies`; regla `only_orchestrator_edits_this_file`; ejemplos genéricos api/ui/infra |
| `claude-progress.md` | `resources/templates/claude-progress.md` | Deslindado de `STATE.md` (posición en el bucle vs. evidencia por sesión); campo de sub-agentes lanzados y artefactos `.planning/` tocados |
| `session-handoff.md` | `resources/templates/session-handoff.md` | Sección "GSD Loop Position" (paso del bucle, waves pendientes) y brief sugerido para la próxima sesión |
| `clean-state-checklist.md` | `resources/templates/clean-state-checklist.md` | Ítems extra: `STATE.md` coherente, sin artefactos `.planning/` huérfanos, resultados de sub-agentes fusionados o registrados |
| `evaluator-rubric.md` | `resources/templates/evaluator-rubric.md` | Reorientada al sub-agente verificador (evidencia citada por fila); conserva la nota de calibración (3-5 rondas) del curso |
| `quality-document.md` | `resources/templates/quality-document.md` | Capas re-mapeadas de Electron a API Python / React / contratos compartidos / infra Cloud Run; conserva el tie-in de simplificación del harness |
| `subagent-brief.md` | `skills/harness-creator/references/multi-agent-pattern.md` (Template: Worker Prompt Structure) | Estructura de brief autocontenido + presets por rol (researcher/planner/executor/verifier) alineados con los agentes GSD |
| `method-map.md` | `resources/reference/method-map.md` | Tres modos de fallo nuevos propios de la arquitectura multi-agente (context rot del orquestador, drift de sub-agente, conflictos entre waves) |

## Qué NO se ha copiado y por qué

- `CLAUDE.md` del curso: redundante con `AGENTS.md`; en el repo destino basta
  un `CLAUDE.md` de una línea que apunte a `AGENTS.md`, o usar solo uno de los dos.
- Plantillas de `.planning/` (STATE/CONTEXT/PLAN/RESEARCH/VERIFICATION): las
  provee el propio GSD; duplicarlas crearía dos fuentes de verdad.
- `reference/coding-agent-startup-flow.md` e `initializer-agent-playbook.md`:
  su contenido ya está integrado en el Startup Workflow y el End Of Session de
  `AGENTS.md`; copiarlos aparte duplicaría instrucciones.
- `reference/prompt-calibration.md`: es una guía de estilo (qué mantener en el
  fichero raíz vs. qué mover fuera), no una plantilla; su regla operativa está
  aplicada en el diseño de `AGENTS.md`.

## Instalación en el repo destino

1. Copiar estos ficheros a la raíz del repo (ajustar `BACKEND_DIR`/`FRONTEND_DIR`
   y los comandos de `init.sh`).
2. Sustituir las features de ejemplo de `feature_list.json` por las reales.
3. `chmod +x init.sh` y verificar que pasa en un checkout limpio.
4. Validar con `validate-harness.mjs` de la skill (ver
   `output/harness-creator-eval.md`) — objetivo ≥ 70/100 antes de la primera
   sesión larga.
