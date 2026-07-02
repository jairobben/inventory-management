# Method Map

This table maps the most common long-running coding-agent failure modes to the
artifact or operating rule that usually fixes them first, in an
orchestrator + ephemeral-subagents harness over GSD.

| Failure mode | What it looks like in practice | Primary fix | Supporting artifact |
| --- | --- | --- | --- |
| Cold-start confusion | A new session spends most of its time rediscovering setup and status | Make the repository the system of record | `claude-progress.md` + `.planning/STATE.md` |
| Scope sprawl | The agent starts several features and finishes none of them cleanly | Restrict active scope | `feature_list.json` |
| Premature completion | The agent claims done after code edits but before runnable proof | Bind completion to evidence | `clean-state-checklist.md`, `evaluator-rubric.md` |
| Fragile startup | Every session re-learns how to boot the project | Standardize setup and verification | `init.sh` |
| Weak handoff | The next session cannot tell what is verified, broken, or next | End with an explicit handoff | `session-handoff.md` |
| Subjective review | Review quality depends on taste or memory | Score output with fixed categories | `evaluator-rubric.md` |
| Context rot in the main session | Long orchestration degrades quality; early decisions get contradicted | Delegate heavy work to fresh-context subagents; orchestrator stays lean | `subagent-brief.md`, GSD phase loop |
| Subagent drift | A spawned worker reopens settled decisions or edits files owned by another plan | Self-contained briefs with explicit constraints and tool allowlists | `subagent-brief.md`, `PLAN-*.md` |
| Conflicting parallel work | Two executors in a wave touch the same concern | Dependency-ordered waves with non-overlapping file lists | GSD plan-checker, `PLAN-*.md` |

## Operating Principle

Add the smallest artifact that directly addresses the observed failure mode.
Avoid solving every reliability problem by dumping more text into one global
instruction file.
