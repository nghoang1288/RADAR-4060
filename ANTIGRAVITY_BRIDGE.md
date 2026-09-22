# RADAR-4060 Antigravity Bridge

This control plane belongs only to `nghoang1288/RADAR-4060`.

## Isolation rule

RADAR-4060 is completely independent from `nghoang1288/Prima`.

Antigravity must not read tasks from Prima, write RADAR receipts/results to Prima, use Prima branches as a bridge, or copy patient/project artifacts between the two repositories.

## Branch roles

- `main`: reviewed RADAR-4060 code.
- `agent-control`: immutable Antigravity tasks plus receipts/results for RADAR-4060 only.
- `antigravity/<task-id-lowercase>`: implementation branches.

## Polling contract

Every 300 seconds:

1. Fetch `origin/agent-control` and `origin/main`.
2. Re-read this file from `origin/agent-control`.
3. Enumerate `.antigravity/tasks/*.json` in lexical order.
4. Ignore tasks whose `target_agent` is not `antigravity`.
5. Ignore a task if a terminal result already exists at `.antigravity/results/<task_id>.json`.
6. Before non-trivial work, write and push `.antigravity/receipts/<task_id>.json` with status `claimed`.
7. Execute the exact branch/SHA requested by the task. Never silently substitute a newer upstream commit.
8. Run the acceptance checks.
9. Write a terminal result with `success`, `failed`, or `blocked`.
10. Push receipts/results only to `agent-control`.
11. If no new task exists, do nothing and create no commit.

## Bootstrap exception

The repository was initialized with a temporary README commit only so this control branch could exist.

Task `RADAR-20260922-001` is allowed a ONE-TIME replacement of `main` with the exact pinned upstream RADAR commit specified in that task. This bootstrap replacement must use the exact SHA and must be recorded in the result.

After that one bootstrap replacement:
- never force-push `main`;
- all code changes go through implementation branches and PRs;
- do not merge a PR unless a later task explicitly requests it.

## Data safety

Never commit or upload:
- patient DICOM;
- patient NIfTI;
- PHI;
- patient screenshots;
- patient predictions;
- patient HTML reports;
- model checkpoints.

Only source code, documentation, synthetic tests, upstream-public demo-compatible material when license permits, and aggregate benchmark metrics may be pushed.

## Result content

Results may contain:
- task status;
- exact code/upstream SHA;
- branch and PR;
- package/runtime versions;
- aggregate peak VRAM/RAM and timing;
- test names and pass/fail counts;
- concise blockers and recommended next action.

Do not place patient-derived outputs or raw clinical predictions in GitHub results.
