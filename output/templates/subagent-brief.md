# Subagent Brief Template

Structure for every ephemeral subagent the orchestrator spawns. Subagents
start with **zero context inheritance**: only what is written here (and what
is on disk in `.planning/`) exists for them. "Based on your findings" is an
anti-pattern — the orchestrator must digest findings into a precise spec
before dispatching.

```markdown
# Self-Contained Worker Brief

## Context (copied from orchestrator synthesis)

**Task**: <one-sentence bounded task>
**Background**: <the 2-5 facts from research/prior work the subagent needs>
**Decisions already made**: <settled choices from CONTEXT.md — do not reopen them>

## Inputs on disk

- `.planning/phases/<phase>/CONTEXT.md`
- `.planning/phases/<phase>/RESEARCH.md`
- `.planning/phases/<phase>/PLAN-<nn>.md`   <- your plan
- <specific source files or directories relevant to the task>

## Your Role

You are an **<researcher | planner | executor | verifier>**. <one sentence on
what that role produces>.

## Constraints

- Use existing patterns from `<path>`.
- Do NOT modify `<files owned by other plans in this wave>`.
- Stay inside the plan's file list; a blocker outside it is reported, not fixed.
- Add tests for success and failure cases (executors).

## Your Tools

- <tool allowlist — researcher/verifier: read-only; executor: read + edit + test>
- Shell: <exact allowed commands, e.g. "pytest", "npm test -- --run" only>

## Verification before reporting done

- <exact commands to run and expected result>

## Deliverable

Return:
1. <primary artifact: findings / PLAN.md files / implementation diff + commit / VERIFICATION.md>
2. Verification results (pass/fail with output snippet)
3. Any blockers or clarifications needed

**Do NOT return**: research tangents, architectural debates, alternative
designs, or work outside the plan.
```

## Role presets

| Role | Reads | Writes | Tools |
|------|-------|--------|-------|
| Researcher | codebase, docs, ecosystem | `RESEARCH.md` | read/search only |
| Planner | `CONTEXT.md`, `RESEARCH.md` | `PLAN-*.md` | read/search only |
| Executor | its `PLAN-*.md` + listed sources | code + atomic commits, plan summary | read/edit/test |
| Verifier | phase goal, `CONTEXT.md`, plans, summaries | `VERIFICATION.md`, fix plans | read/test only |
