## Findings (written after the full run; the tables below are generated)

**Headline (core: Claude Code or Kairos on claude-haiku-5-5, effort low, 30 tasks x 2 repeats = 60 runs each):**

- Success: Kairos native 100% (94-100), Playwright MCP 98% (91-100), cloak-mcp 97% (89-99), devinwangd 83% (72-91).
  The first three are within noise of each other (1-2 runs apart; with 60 runs per config, gaps under ~10 points
  are noise). devinwangd's gap is entirely dialogs: all 10 of its dialog runs (alert, alert on page load, confirm,
  prompt, and the-internet's JS prompt) froze until the 5-minute kill. It failed nothing else.
- Hangs: cloak-mcp 0/60, Kairos 0/60, Playwright MCP 1/60 (after finishing the task), devinwangd 10/60.
- Tool errors per run: cloak-mcp 0.07 (lowest), Kairos 0.18, Playwright MCP 0.25, devinwangd 0.30.
- Tokens per successful task: Kairos 35.6k, cloak-mcp 35.8k, Playwright MCP 38.6k, devinwangd 75.1k (about 2x: its
  80-tool schema is 13.2k tokens on every request, vs 3.4k for cloak-mcp).
- Tool calls per task: cloak-mcp 4.5, Kairos 4.6, Playwright MCP 5.8, devinwangd 5.9.
- Median wall clock: Playwright MCP 8 s, Kairos 10 s, cloak-mcp 11 s, devinwangd 11 s. Confounded: every layer but
  Playwright MCP uses humanized (deliberately slower) mouse and keyboard input.
- The Haiku >100K-token price tier was never hit: 0 of 1,822 API requests in the full run (all configs). Claude Code
  refuses MCP results over its own output limit (Playwright MCP's 423k-character snapshot of the 2,000-row table came
  back as an error and was saved to a file), and cloak-mcp and Kairos cap snapshots, so no prompt grew past 100K.
- Total spend for the whole project: see "Spend by model" below.

**Where cloak-mcp and Kairos lose:**

1. *Large pages, tokens (cloak-mcp).* cloak-mcp used the most tokens per successful large-page task: 117k, vs 42k
   for Playwright MCP, 83k for devinwangd and 94k for Kairos. cloak-mcp's `browser_navigate` inlines the page
   snapshot (capped at 30,000 characters, about 10k tokens) on every navigation, while Playwright MCP 0.0.86 returns
   only a link to a snapshot file on navigate and offers `browser_find`. The gap is driven by `large-archive` (383k
   input tokens per run on average, 14 calls), where the agent reloaded the 600-row page several times to check its
   work. Part of that is a fixture weakness (below), but each reload cost cloak-mcp ~10k tokens and Playwright MCP
   almost nothing. Playwright MCP was also cheaper on `large-article` and `large-order-status`.
2. *Large pages, tokens (Kairos).* Kairos was second-most expensive on large pages (94k per success), mainly
   `large-country` (183k, 15 calls) and `large-archive` (178k).
3. *Speed.* Playwright MCP has the lowest median time (8 s vs 11 s for cloak-mcp). Expected from humanized input, so
   not evidence against the MCP layer, but it is a real cost for users.
4. *Tool errors (Kairos).* Kairos had more tool errors per run (0.18) than cloak-mcp (0.07): failed `fill_form` on
   a styled checkbox (CloakBrowser's humanize engine could not identify the element), stale `select` after a
   postback, and a `browser_console` call that timed out after 120 s.
5. *`pub-quotes-author` (cloak-mcp 0/2).* Both cloak-mcp runs answered "July 12, 1904 in Parral, Chile" for a
   date-of-birth question. The aria snapshot merges the date and birthplace spans into one text line (Kairos's
   snapshot does the same, and its Haiku runs answered with the date only). This is mostly the task's wording
   ("exactly as written there") and the strict checker; see Checker sensitivity.
6. *Kairos with other models (bonus, not head-to-head).* gpt-6-luna filled the late-applying project-name field
   twice; Kairos reported "Filled 1 field(s)" both times but the page stored "Oriomn". Kairos's fill does not verify
   the value on inputs that apply typed text asynchronously.

**The 5 most informative failures** (full transcripts in `results/raw/transcripts/`):

1. `full.cc-devin.claude-haiku-5-5.dialogs-draft.r1`: devinwangd's `browser_click` on "Save draft" (which fires
   `alert()`) never returned, and a parallel `browser_take_screenshot` hung too; killed at 300 s. On the same task
   cloak-mcp's click returned in 0.97 s with "The action opened a dialog ... alert "Draft saved as #4821" is
   blocking the page", then `browser_handle_dialog` (0.33 s), type, click: done in about 9 s.
2. `full.cc-devin.claude-haiku-5-5.dialogs-welcome.r2`: alert fired 0.8 s after load. `browser_navigate` and
   `browser_wait_for` returned, then `browser_snapshot` hung for the rest of the 5 minutes. cloak-mcp and Kairos
   report the open dialog in the next tool result instead.
3. `full.cc-playwright.claude-haiku-5-5.large-archive.r1`: Playwright MCP's only hang. The ticket was archived
   (event logged, so the run counts as a success), then `browser_network_request` (index 3, response body) never
   returned and the run hit the 5-minute limit.
4. `full.kairos.gpt-6-luna.dyn-spa-create.r2`: two `browser_fill_form` calls on an async-state input both reported
   success; the app stored "Oriomn" instead of "Orion", and the agent reported done (see loss 6).
5. `full.cc-cloak.claude-haiku-5-5.pub-quotes-author.r1`: cloak-mcp's only failure type; the merged snapshot line
   "Born: July 12, 1904 in Parral, Chile" was copied whole into the answer (see loss 5).

**Caveats and harness notes:**

- Scoring is the pre-written checker only. A run that finished the task and then hung counts as a success and as a
  timeout (one case: Playwright MCP `large-archive.r1`).
- `large-archive` fixture weakness: archiving posts to the server and shows "Saved." but leaves the row in the table,
  so agents in every config spent extra calls verifying. Same fixture for all configs; it inflates token counts on
  that task, most for layers that inline snapshots on navigation.
- Checker strictness: 6 answer-task failures would pass a looser "contains" check (listed below); the official
  score keeps the exact check written before the runs.
- Provider stalls: 2 runs (both OpenAI models) waited ~295 s on the API with no tool running; they were logged in
  `api_errors.jsonl`, re-queued and rerun, as the harness rule says. No Anthropic API errors.
- Claude Code output tokens are taken from each run's final result (stream-json undercounts them per message). Runs
  killed before a final result (timeouts) keep the undercount; input and cache tokens are exact.
- devinwangd runs with `--caps all --humanize` (the 80-tool setup cloak-mcp replaced); its default is 34 tools
  (6,956 schema tokens). Playwright MCP 0.0.86 runs with `--isolated` on the same CloakBrowser binary and ships an
  alpha Playwright.
- Kairos is driven by subclassing its `Agent` with only its browser tools (no Kairos file changed); it is a
  different client from Claude Code, so Kairos-vs-Claude-Code rows mix client and browser-layer effects.

