# Evaluación — skill `harness-creator` (learn-harness-engineering)

- **Fuente**: `harness-course/skills/harness-creator/` (mirror de [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering)).
- **Método**: ejecución real de `create-harness.mjs` y `validate-harness.mjs` contra un proyecto Node dummy en `./sandbox` (package.json con `test`/`lint`/`build`, 1 test pasando con `node --test`), más casos de control: directorio vacío, repo con solo `CLAUDE.md`, y un monorepo Python+React.
- **Fecha**: 2026-07-02. Node v22.

## Estructura de la skill

```
skills/harness-creator/
├── SKILL.md                  # instrucciones para el agente (cuándo y cómo usarla)
├── README.md
├── metadata.json
├── evals/evals.json          # casos de eval de la propia skill
├── references/               # 7 patrones: multi-agent, context-engineering,
│                             #   memory-persistence, lifecycle-bootstrap,
│                             #   skill-runtime, tool-registry, gotchas
├── scripts/
│   ├── create-harness.mjs        # scaffolding (75 líneas)
│   ├── validate-harness.mjs      # scoring (43 líneas)
│   ├── run-benchmark.mjs         # self-check + score + eval coverage
│   ├── render-assessment-html.mjs
│   └── lib/harness-utils.mjs     # toda la lógica (440 líneas)
└── templates/                # agents.md, feature-list.json (+schema),
                              #   progress.md, session-handoff.md, init.sh
```

Cero dependencias npm: solo `node:fs`/`node:path`. Se ejecuta directamente sin instalación.

## Qué hace `create-harness.mjs`

1. **Detecta el stack** recorriendo hasta 800 ficheros (ignora `.git`, `node_modules`, etc.): si hay `package.json` → `typescript-react` / `typescript` / `node`; si no, busca `pyproject.toml`/`requirements.txt` (python), `go.mod`, `Cargo.toml`, `pom.xml`, gradle, `.csproj`. Detecta también el package manager por lockfile.
2. **Deriva comandos de verificación**: para Node lee los `scripts` reales del `package.json` (`check`, `typecheck`, `lint`, `test`, `build`); para Python usa `pytest || [ $? -eq 5 ]` (tolera "no tests") + `compileall` excluyendo venvs.
3. **Genera 5 ficheros** desde plantillas con placeholders (`{{VERIFICATION_COMMANDS}}`, etc.): `AGENTS.md` (o `CLAUDE.md` con `--agent-file`), `feature_list.json` (5 features placeholder encadenadas por `dependencies`), `progress.md`, `session-handoff.md`, `init.sh` (ejecutable, `set -e`, un bloque `echo === cmd ===` por comando).
4. **Es idempotente y no destructivo**: ficheros existentes → `SKIPPED (exists)`; sobrescribir requiere `--force`.

### Resultado contra el sandbox

Detectó `stack: node`, derivó `npm install` + `npm run lint` + `npm test` + `npm run build` (los scripts reales del dummy), escribió los 5 ficheros, y el `init.sh` generado pasó de punta a punta (exit 0). La re-ejecución marcó los 5 como `SKIPPED`.

## Qué puntúa `validate-harness.mjs`

Puntúa **5 subsistemas × 5 checks booleanos** cada uno. Score de subsistema = `max(1, round(passed/5 * 5))`; overall = suma/25 en %; **bottleneck** = subsistema de menor score (o `none` si todo está a 5). Exit code 1 si overall < `--min-score` (default **70**). Soporta `--json` y `--html`.

Solo lee **7 ficheros por nombre exacto en la raíz**: `AGENTS.md`, `CLAUDE.md`, `feature_list.json`, `feature-list.json`, `progress.md`, `session-handoff.md`, `init.sh`.

| Subsistema | Checks (resumen) |
|---|---|
| instructions | existe AGENTS/CLAUDE.md; documenta startup workflow, definition of done, comandos de verificación; enruta a los ficheros de estado |
| state | existe feature tracker; JSON válido con `features[].{id,name,description,status}`; existe progress.md; progress soporta restart; handoff captura blockers/files/next |
| verification | existe init.sh; `set -e` (fail fast); comando de test documentado; check estático/build; evidencia de verificación registrada |
| scope | regla one-feature-at-a-time; `dependencies` en el tracker; `status` explícito; scope boundary; completion gate |
| lifecycle | init.sh; procedimiento end-of-session; session-handoff.md; marcadores de restart; ruta de restart limpia |

Dos detalles de implementación relevantes:

- **Anti-gaming**: los checks de instrucciones usan `structuredHas()`, que solo cuenta keywords que aparecen en **líneas estructurales** (headings, listas, tablas, bold lead-ins, código) — sembrar las palabras clave en prosa suelta no puntúa.
- **Suelo de 20/100**: cada subsistema puntúa mínimo 1, así que un directorio vacío da 20/100 (comprobado), no 0.

### Resultados medidos

| Target | Overall | Bottleneck | Exit |
|---|---|---|---|
| `./sandbox` recién generado por `create-harness` | **100/100** | none | 0 |
| Directorio vacío | 20/100 | instructions | 1 |
| Repo real con solo un `CLAUDE.md` convencional | 24/100 | state | 1 |

`run-benchmark.mjs` añade un self-check (scaffolds un harness desechable y lo valida, probando que los scripts funcionan end-to-end) y una métrica de cobertura de evals (10/10 en nuestra ejecución).

## Limitaciones encontradas (relevantes para el repo destino)

1. **Circularidad generador–validador.** El 100/100 del sandbox no mide calidad: generador y validador comparten vocabulario y nombres de fichero. Mide *conformidad estructural con su propia convención*. El propio SKILL.md lo admite: "this is a structural benchmark… real effectiveness still needs before/after agent sessions".
2. **Monorepo Python+React: detección parcial.** Con `backend/requirements.txt` + `frontend/package.json` (sin package.json raíz) detecta `stack: python` y genera un `init.sh` que **ignora el frontend por completo**. Para el repo destino habría que pasar `--commands` a mano o editar el `init.sh` generado (nuestro `output/templates/init.sh` ya cubre los dos stacks).
3. **No valida contenido, solo estructura.** Un `feature_list.json` lleno de placeholders puntúa igual que uno real; `evidence: []` vacío pasa el check de evidencia porque la *palabra* "Evidence" aparece en las plantillas.
4. **Nombres de fichero rígidos y en raíz.** Un repo GSD guarda el estado en `.planning/STATE.md` — el validador no lo ve y puntuaría `state` bajo aunque la continuidad real sea excelente. Keywords en inglés: un harness redactado en otro idioma falla los checks textuales.
5. **Incoherencia interna del propio curso.** `tools/audit-harness.sh` (el auditor shell del mismo repo) exige `PROGRESS.md` en mayúsculas y artefactos extra (`.harness/arch-rules.json`, sprint contracts, session traces): el harness generado por la propia skill **suspende el audit del mismo curso** (5/7 críticos). Son dos varas de medir distintas; conviene elegir una.

## Recomendación

**Sí instalarla en un repo real, con rol acotado**: es pequeña, sin dependencias, no destructiva y honesta sobre lo que mide. Concretamente:

- **Usar `create-harness.mjs` una sola vez** como scaffold inicial en repos que no tengan harness — y en el repo destino, con `--commands` explícitos o sustituyendo su `init.sh` por el de `output/templates/` (dos stacks).
- **Usar `validate-harness.mjs` como smoke check estructural en CI** (`--min-score 70`, exit code + `--json`), entendiéndolo como checklist de los 5 subsistemas, no como métrica de calidad. No perseguir el 100/100.
- **Para el harness GSD del repo destino**: o se mantienen los 7 nombres canónicos en raíz como *fachada* (ficheros finos que enlazan a `.planning/`), o se adapta `loadHarnessFiles()`/los checks al layout GSD (~30 líneas). Sin una de las dos cosas, el score de `state`/`lifecycle` será ruido.
- **Las `references/` valen más que los scripts** para nuestro caso: `multi-agent-pattern.md` (briefs autocontenidos, coordinator vs. fork vs. swarm, tool allowlists por rol) y `context-engineering-pattern.md` describen exactamente la arquitectura orquestador + efímeros que vamos a montar. Ya está destilado en `output/templates/subagent-brief.md`.
