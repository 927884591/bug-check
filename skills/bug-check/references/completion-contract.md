# Completion Contract

Final bug-fix reports must prove closure of the original path and the AI-selected boundary cards. A broad lint/test pass is not a substitute for boundary evidence.

```text
Root cause:
Changed files:
Context pack source:
Matched boundary cases:
Boundary handling table:
Original path verification:
Boundary verification:
Checks run:
Remaining risks:
```

Boundary handling table:

| Boundary | Status | Evidence | Action |
|---|---|---|---|
| ui-list-table | missing -> fixed | page reset did not happen on filter change | added reset + test |
| api-contract | already handled | API client preserves filter params | no change |
| tenant-isolation | not applicable | no tenant context in this flow | no change |

Allowed statuses:

- `relevant`
- `already handled`
- `missing -> fixed`
- `not applicable`

Minimum evidence:

- `Root cause:` names the failed mechanism, not only the symptom.
- `Changed files:` lists the files or clearly states no code files changed.
- `Context pack source:` says whether it came from `build-bug-context.py`, manual routing, explicit changed files, or user-provided report.
- `Matched boundary cases:` lists every boundary card the AI selected and loaded from the context pack, plus any manual boundary key when no card fit.
- `Boundary handling table:` includes one row per matched card.
- `Original path verification:` states how the original failure path was reproduced/traced and verified.
- `Boundary verification:` states checks for every boundary marked `missing -> fixed`, and records skipped relevant checks as risk.
- `Checks run:` lists actual commands or manual runtime checks.
- `Remaining risks:` names unverified cases or says none after evidence.
