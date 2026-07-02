# Evaluator Rubric

Used by the **verifier subagent** (and by humans at milestones) after
implementation and before final acceptance of a phase or feature. The verifier
receives this rubric inside its brief and must return one score per row with a
one-line justification citing evidence (command output, diff, artifact).

| Category | Question | Score (0-2) | Notes |
| --- | --- | --- | --- |
| Correctness | Does the implemented behavior match the phase goal and the decisions in `CONTEXT.md`? |  |  |
| Verification | Did the required checks actually run, with recorded evidence (not claims)? |  |  |
| Scope discipline | Did the executor stay inside its PLAN.md / feature scope? |  |  |
| Reliability | Does the result survive `./init.sh` from a clean checkout and a restart? |  |  |
| Maintainability | Is the code and documentation clear enough for the next fresh-context agent? |  |  |
| Handoff readiness | Can a fresh session continue work from repo artifacts only (`.planning/`, progress log, feature list)? |  |  |

## Verdict

- Accept
- Revise
- Block

## Required Follow-Up

- Missing evidence:
- Required fixes (as targeted fix plans, one per discrepancy):
- Next review trigger:

## Tuning note (do not delete)

Out of the box, agents are poor self-judges — they identify issues and then
talk themselves into approving. Calibrate this rubric against human judgment:

1. Run the evaluator on a completed phase.
2. Compare its scores against your own review.
3. Where they diverge, make the pass/fail criteria of that row more specific.
4. Re-run and check alignment. Plan for 3-5 tuning rounds; record each change.
