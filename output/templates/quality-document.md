# Quality Document

A quality snapshot for each product domain and architectural layer. Agents and
humans use this to know where the codebase is strong and where it needs work.
The evaluator rubric scores individual sessions; this file scores the codebase
itself over time.

**Update cadence:** after each significant session, before benchmark
comparisons, after cleanup passes, and when onboarding a new agent or model.

**Grading scale:**

- **A**: All verification passing, clean architecture, agent-legible, stable tests
- **B**: Verification passing, mostly clean, minor gaps in legibility or test coverage
- **C**: Partially working, known gaps, some code areas hard for agents to understand
- **D**: Not working, or major structural issues

---

## Product Domains

Replace the placeholder rows with your product's actual domains.

| Domain | Grade | Verification | Agent Legibility | Test Stability | Key Gaps | Last Updated |
|--------|-------|-------------|-----------------|---------------|----------|-------------|
| (domain 1) | - | - | - | - | - | - |
| (domain 2) | - | - | - | - | - | - |
| (domain 3) | - | - | - | - | - | - |

## Architectural Layers

Pre-filled for a Python API + React frontend on Cloud Run; adjust to match the
target repo's real layering.

| Layer | Grade | Boundary Enforcement | Agent Legibility | Key Gaps | Last Updated |
|-------|-------|---------------------|-----------------|----------|-------------|
| API layer (routes/controllers) | - | - | - | - | - |
| Domain/services (Python) | - | - | - | - | - |
| Data access / persistence | - | - | - | - | - |
| Frontend views (React) | - | - | - | - | - |
| Frontend state & API client | - | - | - | - | - |
| Shared contracts (schemas/types) | - | - | - | - | - |
| Infra & deploy (Cloud Run, CI) | - | - | - | - | - |

## Change History

### YYYY-MM-DD

- Changes:
- Domains promoted:
- Domains demoted:
- New gaps identified:
- Gaps closed:

## Harness simplification tie-in

Every harness component encodes an assumption about what the model cannot do;
these assumptions go stale as models improve. To check whether a component is
still needed: snapshot this document, remove one component, run the benchmark
task suite, snapshot again. If grades didn't drop, the component was overhead;
if they did, restore it.
