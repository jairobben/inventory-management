# Session Handoff

Compact handoff between orchestrator sessions. Fill at the end of any session
that is large, mid-phase, or leaves anything unverified. The next session must
be able to continue from this file + `.planning/` + `feature_list.json` alone.

## Verified Now

- What is currently working:
- What verification actually ran (exact commands + result):

## GSD Loop Position

- Milestone / phase:
- Loop step reached (Discuss / Plan / Execute / Verify / Ship):
- Plans completed vs. pending in this phase:
- Waves merged / outstanding executor results:

## Changed This Session

- Code or behavior added (by which subagent):
- Infrastructure or harness changes:
- `.planning/` artifacts written:

## Broken Or Unverified

- Known defect:
- Unverified path (e.g. frontend built but not exercised in browser):
- Risk for the next session:

## Next Best Step

- Highest-priority unfinished feature (id):
- Why it is next:
- What counts as passing:
- What must not change during that step:
- Suggested subagent brief (or pointer to the PLAN.md that covers it):

## Commands

- Startup: `./init.sh`
- Backend verification:
- Frontend verification:
- Focused debug command:
