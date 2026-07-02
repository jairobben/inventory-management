# Clean State Checklist

Run before ending every orchestrator session. A session is not complete until
all items pass.

## Baseline

- [ ] `./init.sh` still passes end to end (backend + frontend).
- [ ] The production build of the frontend succeeds.
- [ ] No debug artifacts left behind (print/console.log noise, temp files, commented-out blocks).

## State files

- [ ] `claude-progress.md` has an entry for this session with evidence.
- [ ] `feature_list.json` reflects what is actually passing vs. unverified
      (no false `passing`, at most one `in_progress`).
- [ ] `.planning/STATE.md` matches reality (phase, completed plans, blockers).
- [ ] No orphan `.planning/` artifacts (plans for abandoned work are marked or removed).

## Handoff

- [ ] No half-finished step is left undocumented.
- [ ] All spawned subagent results are either merged or recorded as pending in the handoff.
- [ ] `session-handoff.md` filled in if the session was large or mid-phase.
- [ ] Work is committed with a descriptive message; repo is safe to resume.
- [ ] The next session can continue without manual repair.
