# AGENTS.md — Orchestrator Operating Manual

This repository runs a **single-orchestrator harness**: one long-lived
orchestrator session coordinates the work, and all heavy tasks (research,
planning, implementation, verification) are delegated to **ephemeral
subagents** that start with a fresh context and terminate when done.
Planning state lives in `.planning/` (GSD conventions, fork of
`open-gsd/get-shit-done-redux`).

The goal is not to maximize raw code output. The goal is to leave the repo in
a state where the next session can continue without guessing.

## Orchestrator Rules (non-negotiable)

- The orchestrator **never edits source files directly**. It spawns subagents,
  synthesizes their results, updates shared state, and routes to the next step.
- Subagents receive **self-contained briefs** (see `subagent-brief.md`). Never
  say "based on your findings" — digest findings into a precise spec first.
- Subagents in the same wave must touch **non-overlapping concerns**.
- Anything a subagent needs must be **on disk before it is spawned**
  (`.planning/` artifacts, not conversation history).
- One phase in progress at a time. One active feature per executor.

## Startup Workflow

Before any delegation:

1. Confirm the working directory with `pwd`.
2. Read `.planning/STATE.md` — current milestone, phase, and pending plans.
3. Read `claude-progress.md` for the latest verified state and next step.
4. Read `feature_list.json` and identify the highest-priority unfinished feature.
5. Review recent commits with `git log --oneline -5`.
6. Run `./init.sh` (installs deps, runs baseline verification for both stacks).

If baseline verification is already failing, fix that first (spawn a repair
subagent). Do not stack new feature work on top of a broken starting state.

## Working Rules

- Work on one feature at a time; map each feature to a GSD phase or plan.
- Do not mark a feature complete just because a subagent reported success —
  require the verification evidence in its deliverable.
- Keep changes within the selected feature scope unless a blocker forces a
  narrow supporting fix.
- Do not silently change verification rules during implementation.
- Prefer durable repo artifacts (`.planning/`, `feature_list.json`,
  `claude-progress.md`) over chat summaries.

## Required Artifacts

- `.planning/STATE.md`: GSD navigation layer — where the project sits in the loop
- `.planning/phases/<phase>/{CONTEXT.md,RESEARCH.md,PLAN-*.md,VERIFICATION.md}`:
  per-phase artifacts produced by the loop
- `feature_list.json`: source of truth for feature state and scope boundaries
- `claude-progress.md`: session log and current verified status
- `init.sh`: standard startup and verification path
- `session-handoff.md`: compact handoff between orchestrator sessions

## Definition Of Done

A feature is done only when all of the following are true:

- the target behavior is implemented
- the required verification actually ran (backend, frontend, and — when the
  phase touches deploy config — a deploy dry run)
- evidence is recorded in `feature_list.json` or `claude-progress.md`
  (command + output, not a claim)
- `VERIFICATION.md` for the phase covers requirement and decision coverage
- the repository remains restartable from the standard startup path

## Verification Commands

```bash
# Full verification (recommended)
./init.sh
```

Required checks (also runnable individually — keep in sync with init.sh):

- Backend: `<pytest command>` and `<lint/type-check command>` (e.g. ruff, mypy)
- Frontend: `<test command>`, `<lint command>`, `<build command>`
- Deploy surface (only when touched): `<gcloud/terraform dry-run or config validation>`

## End Of Session

Before ending an orchestrator session:

1. Update `claude-progress.md` (sessions, evidence, risks).
2. Update `feature_list.json` and `.planning/STATE.md`.
3. Fill in `session-handoff.md` if the session was large or is mid-phase.
4. Run the clean-state checklist (`clean-state-checklist.md`).
5. Commit with a descriptive message once the work is in a safe state.
6. Leave the repo clean enough for the next session to run `./init.sh`
   immediately.

## Escalation

- **Architecture decisions**: record in the phase `CONTEXT.md`; ask the user if unsettled.
- **Repeated verification failures** (3+ attempts on the same failure): stop,
  record in progress log, flag for human review.
- **Scope ambiguity**: re-read `feature_list.json` and the phase goal; when in
  doubt, split the phase.
