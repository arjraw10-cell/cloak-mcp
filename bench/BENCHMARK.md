# Browser MCP benchmark

Question: when an AI agent drives a browser, does **cloak-mcp** (and Kairos's built-in browser tools) finish
more tasks, with fewer errors and tokens, than **@devinwangd/cloak-browser-mcp** and **Playwright MCP**?

## Matrix

Core comparison, all on `claude-haiku-5-5`, effort `low` (only the browser layer differs):

| config | client | browser layer |
|---|---|---|
| `cc-cloak` | Claude Code (`claude --bare -p`) | cloak-mcp (default flags: headed, humanized, ephemeral) |
| `cc-devin` | Claude Code | @devinwangd/cloak-browser-mcp `--caps all --humanize` (the 80-tool setup cloak-mcp replaced) |
| `cc-playwright` | Claude Code | @playwright/mcp `--isolated --executable-path <CloakBrowser chrome.exe>` |
| `kairos` | Kairos (Agent class imported) | Kairos native browser tools |

Bonus (Kairos native tools only, not compared head-to-head with Claude Code): `glm-5.3-flash`, `gpt-6-luna`,
`gpt-6.1-sol`, effort `low`.

Every browser is the same CloakBrowser Chromium binary (146.0.7680.177.5), headed, with a fresh ephemeral
profile per run (`CLOAKBROWSER_PROFILES_DIR` points at an empty per-run folder). CloakBrowser input is humanized
for cloak-mcp, devinwangd and Kairos; Playwright MCP has no humanized input, so wall-clock times are confounded.

Claude Code runs load only the browser MCP under test (`--mcp-config <file> --strict-mcp-config`), no built-in
tools (`--tools ""`, so no WebFetch/WebSearch/Bash), MCP tools pre-approved (`--allowedTools mcp__browser
--permission-mode dontAsk`), `--max-turns 31`, `--output-format stream-json --verbose`, `ENABLE_TOOL_SEARCH=false`
(all tool schemas loaded up front), and bill to `ANTHROPIC_API_KEY` from Kairos's `provider.json` (`--bare` never
reads OAuth, so the owner's Claude plan is untouched).

Kairos runs (`kairos_run.py`) subclass Kairos's `Agent` without editing Kairos: the schema offers only the
`browser_*` tools, the browser group starts enabled with the guide `enable_tools` would return appended to the
system prompt, and usage per API request is recorded.

Limits per run: 5 minutes wall clock, 30 tool calls (the 31st call ends the run as `cap`). Run order is shuffled
with seed 2026; up to 4 runs in parallel.

## Tasks

30 tasks in `tasks.py` (22 on local fixtures in `fixtures/`, 8 on toscrape.com and the-internet.herokuapp.com),
6 categories: basic 6, forms 5, dialogs 5, frames-tabs 5, large 5, dynamic 4. Every task has an automatic
checker, written before any run: a normalized match on the `FINAL ANSWER:` line, or a check of the events the
local fixture server (`server.py`) logged for that run's URL token. No LLM judging. All contenders get the same
prompt, with no tool names. `gen_fixtures.py` regenerates the large-page fixtures deterministically.

## Logs

- `results/raw/runs.jsonl`: one record per finished run (status, pass/fail and reason, tokens, cost, wall time).
- `results/raw/calls.jsonl`: one record per tool call (tool, argument size, latency, result size in tokens
  (tiktoken o200k), error flag and text, timed-out flag).
- `results/raw/api_errors.jsonl`: runs that died from API/provider errors (re-queued, not counted as failures).
- `results/raw/transcripts/<run_id>.jsonl` (+ `.err`): the raw Claude Code stream-json / Kairos event stream.
- `results/raw/server_events.jsonl`: everything the fixtures submitted.
- `results/schema_tokens.json`, `results/tool_schemas.json`: static tool-schema cost of each layer (current, i.e.
  cloak-mcp v2); `results/schema_tokens_v1.json`, `results/tool_schemas_v1.json`: the same for v1.
- Phases: `dev` runs are harness checks, `pilot` is 6 tasks x 1 repeat, `full` is the analysed run with cloak-mcp
  v1, `full2` is the identical suite rerun (all configs) with cloak-mcp v2, `full3` reruns only the Kairos configs
  with Kairos v2 (same seeded order: the full 420-run list is shuffled, then filtered), `full4` reruns cc-cloak and
  the Kairos configs with cloak-mcp v2.1 and Kairos v2.1.

Cost = each API response's token usage x the prices in `provider.json` (Haiku 5.5: $0.10 in / $0.50 out per 1M,
$0.50 / $2.50 above 100K prompt tokens; cache reads 0.1x and cache writes 1.25x the input price). The runner
stops launching runs at $18 total.

## Versions

| component | version |
|---|---|
| cloak-mcp v1 (phases pilot, full) | commit 96aa864 (package 0.1.0; cloakbrowser npm 0.5.12, playwright-core 1.63.0, MCP SDK 1.32.1) |
| cloak-mcp v2 (phase full2) | commit 76211fc (large-page snapshot card, `browser_find`, `browser_snapshot` target/depth; same dependencies) |
| cloak-mcp v2.1 (phase full4) | commit 1d22924 (section snapshots keep other refs valid; `browser_find` shows the whole matching row and splits literal "a\|b" searches; outline lists dropdowns) |
| @devinwangd/cloak-browser-mcp | 0.1.4 (cloakbrowser npm 0.3.32, playwright-core 1.65.1, MCP SDK 1.32.2) |
| @playwright/mcp | 0.0.86 (playwright 1.66.0-alpha-2026-11-18) |
| CloakBrowser Chromium | 146.0.7680.177.5 (windows-x64) |
| Claude Code | 2.1.329 |
| Kairos v1 (phases pilot, full, full2) | commit ac28cd7 (branch v4-claude-standby); Python 3.12.3; cloakbrowser 0.6.0, playwright 1.63.0 |
| Kairos v2 (phase full3) | commit 116efbc (large-page card, ref-aware `browser_search_page`, `browser_snapshot` target/depth; same dependencies) |
| Kairos v2.1 (phase full4) | commit 0367e99 (same ref and whole-row fixes, "a\|b" fallback for literal patterns, fast jump before far scrolls) |
| Node.js | 25.6.1 |
| Models | `claude-haiku-5-5` (Anthropic API); `z-ai/glm-5.3-flash` (OpenRouter); `gpt-6-luna`, `gpt-6.1-sol` (OpenAI) |

## Rerun from scratch (on the desktop PC)

```bat
rem 1. Code under test
git clone https://github.com/arjraw10-cell/Kairos2 C:\Users\arjra\Documents\Kairos
cd C:\Users\arjra\Documents\Kairos && git checkout ac28cd7
rem    provider.json (API keys) goes in C:\Users\arjra\Documents\Kairos\ with a claude-haiku-5-5 setup
git clone https://github.com/arjraw10-cell/cloak-mcp C:\Users\arjra\Documents\browser-mcp-bench\vendor\cloak-mcp
cd C:\Users\arjra\Documents\browser-mcp-bench\vendor\cloak-mcp && git checkout 96aa864 && npm ci && npm run build
npx cloakbrowser install

rem 2. Harness dependencies
cd C:\Users\arjra\Documents\browser-mcp-bench
python -m venv .venv
.venv\Scripts\pip install cloakbrowser==0.6.0 fastapi==0.128.0 httpx==0.28.1 openai==2.29.0 playwright==1.63.0 ^
  prompt_toolkit==3.0.52 regex==2026.5.9 rich==15.0.0 tiktoken==0.13.0 uvicorn[standard]==0.40.0 ^
  websockets==15.0.1 psutil==7.1.3 anthropic==2.12.0
.venv\Scripts\pip install -e C:\Users\arjra\Documents\Kairos --no-deps
cd mcp-servers && npm ci && cd ..

rem 3. Static schema cost, then the runs (each launch is a scheduled task in the logged-in desktop session)
.venv\Scripts\python schema_tokens.py
powershell -File launch.ps1 pilot --bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol
.venv\Scripts\python pilot_report.py
powershell -File launch.ps1 full --bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol
.venv\Scripts\python analyze.py full

rem cloak-mcp v2 rerun: check out 76211fc in vendor\cloak-mcp, npm ci && npm run build, then
copy results\schema_tokens.json results\schema_tokens_v1.json & copy results\tool_schemas.json results\tool_schemas_v1.json
.venv\Scripts\python schema_tokens.py
powershell -File launch.ps1 full2 --bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol
.venv\Scripts\python analyze.py full2
.venv\Scripts\python compare.py

rem Kairos v2 rerun: check out 116efbc in C:\Users\arjra\Documents\Kairos, then
.venv\Scripts\python schema_tokens.py kairos-only
powershell -File launch.ps1 full3 --configs kairos --bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol
.venv\Scripts\python analyze.py full3
.venv\Scripts\python compare_kairos.py

rem cloak-mcp v2.1 + Kairos v2.1 rerun: check out 1d22924 in vendor\cloak-mcp (npm ci && npm run build) and 0367e99 in Kairos, then
.venv\Scripts\python schema_tokens.py full4
powershell -File launch.ps1 full4 --configs cc-cloak,kairos --bonus glm-5.3-flash,gpt-6-luna,gpt-6.1-sol
.venv\Scripts\python analyze.py full4
.venv\Scripts\python compare_full4.py
```

`analyze.py full` writes `results/summary.md` (generated tables plus the hand-written findings in
`results/notes.md`). `python analyze.py pilot` writes `results/summary_pilot.md`; `analyze.py full2` writes
`results/summary_full2.md` (with `results/notes_full2.md`); `compare.py` writes `results/compare_v1_v2.md`.
`analyze.py full3` writes `results/summary_full3.md` (with `results/notes_full3.md`); `compare_kairos.py` writes
`results/compare_kairos.md`; `schema_tokens.py kairos-only` writes `results/schema_tokens_full3.json`.
`analyze.py full4` writes `results/summary_full4.md` (with `results/notes_full4.md`); `compare_full4.py` writes
`results/compare_full4.md`; `schema_tokens.py full4` writes `results/schema_tokens_full4.json` (cloak-mcp and Kairos).

`launch.ps1` runs `bench.py` through `schtasks /it` (only when the user is logged on), so the browsers are headed
on the desktop and the run survives SSH disconnects; progress goes to `results/raw/console.log`. Rerunning the
same command resumes: finished runs are skipped, runs that died from API errors are retried.
