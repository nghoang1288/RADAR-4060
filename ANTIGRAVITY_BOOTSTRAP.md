# Antigravity Bootstrap — RADAR-4060

Use this once to move Antigravity from "not watching this repo" to the RADAR-specific control loop.

Repository:
`https://github.com/nghoang1288/RADAR-4060`

Hard rule:
**Do not use Prima for RADAR.**

## One-time local setup

1. Clone or fetch `nghoang1288/RADAR-4060`.
2. Configure a local RADAR workspace, for example:
   - `RADAR_REPO`: local checkout of RADAR-4060;
   - `RADAR_RUNTIME_ROOT`: local WSL/runtime/cache directory.
3. Poll only `origin/agent-control` in this repository for RADAR tasks.
4. Re-read `ANTIGRAVITY_BRIDGE.md` on every poll.
5. Process pending tasks every 300 seconds.

Local machine paths stay outside Git.

## First task

`.antigravity/tasks/RADAR-20260922-001.json`

Claim it, execute it, and push the terminal result to:

`.antigravity/results/RADAR-20260922-001.json`

on `agent-control`.
