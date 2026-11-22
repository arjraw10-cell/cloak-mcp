## Findings for full3 (Kairos v2 = 116efbc, Kairos configs only; written after the run, tables below are generated)

full3 reruns the identical suite (same 30 tasks, checkers, fixtures, prompts, limits; the same seeded order as v1,
filtered to Kairos) with Kairos 116efbc, which ports cloak-mcp v2's large-page handling: a card for snapshots over
8,000 characters, `browser_search_page` over a fresh accessibility snapshot with refs and context, and
`browser_snapshot` target/depth. Full comparison tables: `compare_kairos.md`. Kairos v1 (ac28cd7) ran twice, in
`full` and `full2`; the difference between those two runs is the noise band.

**Kairos on Haiku 5.5 (60 runs each): v1 full / v1 full2 -> v2 full3**

- Success 100% / 97% -> 98%. The one v2 failure is the wrong-row archive described below.
- Hangs 0 / 0 -> 0. Tool errors per run 0.18 / 0.32 -> 0.23.
- Tokens per successful task 35.6k / 39.4k -> 26.1k (-27% to -34%). Large pages 94k / 116k -> 39k (-58% to -66%).
  `browser_navigate` results on large pages: 4.5-4.7k -> 1.4k tokens.
- Tool calls per task 4.6 / 4.8 -> 4.1; on large pages 6.7 / 8.1 -> 5.0.
- Small categories: tokens per success within -7% to +8% of v1 (forms 33.3k/32.3k -> 34.9k is the largest rise),
  inside the v1 noise band (Haiku's own full -> full2 drift was +11% overall and +23% on large pages). The schema
  grew by 116 tokens (3,001 -> 3,117), so no small-page regression worth naming.

**Bonus models (Kairos only), v1 full / full2 -> v2 full3:** glm-5.3-flash success 95% / 95% -> 100%, tokens per
success 20.4k / 23.7k -> 22.0k (no clear change; large 44k / 63k -> 46k, but large success 80% / 90% -> 100%);
gpt-6-luna 92% / 95% -> 92%, 19.2k / 17.4k -> 16.8k (large 48k / 37k -> 33k); gpt-6.1-sol 98% / 97% -> 97%,
18.3k / 19.2k -> 15.2k (large 34k / 39k -> 19k, and $/run 0.0122 -> 0.0106). The large-page savings are smaller
for these models than for Haiku because in v1 they already read large pages with JS or search rather than full
snapshots.

**Large pages vs cloak-mcp v2 (Haiku, tokens per run):** Kairos v2 averages 46k across the 5 large tasks vs 33k
for cloak-mcp v2 in full2. Kairos v2 is cheaper on `large-order-count` (27k vs 47k) and more expensive on
`large-archive` (97k vs 56k), `large-country` (54k vs 34k), `large-article` (31k vs 18k) and `large-order-status`
(22k vs 11k). Part of that gap is the client (Kairos's system prompt is larger than Claude Code's in `--bare`
mode, and it is resent with every request), so the Kairos-vs-Claude-Code comparison mixes client and layer.

**How the new tools were used (all Kairos models, full3):** `browser_search_page` 52 calls in 39 runs (15 by
Haiku), mean result 454 tokens, max 6,425 (v1: 35-39 calls, mean ~70 tokens, since it used to return text lines
only). `browser_snapshot` with target/depth 32 calls in 25 runs, almost all by the bonus models (2 by Haiku), mean
888 tokens, max 5,662. Whole-page `browser_snapshot` dropped from 45-62 calls (mean 700-900 tokens) to 25 calls
(mean 168 tokens).

**Problems found (reported, not fixed; Kairos and cloak-mcp code untouched):**

1. *Search context shows the wrong row's button.* `browser_search_page "T-0842"` prints three lines of context
   before and after the match. The lines before end with the previous row's `button "Archive" [ref=e2655]` (T-0841);
   the lines after stop at `cell [ref=e2660]:`, just before T-0842's own Archive button (e2661). In
   `full3.kairos.claude-haiku-5-5.large-archive.r1` the agent clicked e2655 and archived T-0841, the only
   wrong-row archive in any run of any phase. cloak-mcp v2's `browser_find` (ported from the same Playwright MCP
   code) prints the identical layout; its agents read the row with `browser_snapshot target=` instead and were not
   misled. Showing the whole matched row (or the context after the match first) would remove the trap.
2. *`pattern` is literal by default, and models write regex alternations.* Kairos-Haiku passed patterns like
   `"rebuilt|Harrow Point|rebuild"` with `regex` off in 5 of its 10 large-page runs; each came back "No matches",
   with a hint about collapsed content that did not apply. Agents recovered with JS or a second search, but
   gpt-6-luna on `large-country.r2` gave up after two such misses, never clicked Save and reported "done" (fail).
   The parameter name `pattern` suggests a regex; cloak-mcp's equivalent did not show this problem in full2.
3. *The known humanized-scroll click timeout now hits every run of `large-archive`.* All 8 full3 runs of that task
   (all models) had a first `browser_click` fail with `ElementHandle.click: Timeout 10000ms exceeded` (~12.4 s,
   the Archive button is ~3,600 px down). With v1 code it hit 0/8 runs in `full` and 2/8 in `full2` (plus one
   `Locator.element_handle` timeout on Haiku `large-country` in full2). The cause is the same pre-existing bug; v2
   makes it frequent because search hands the agent a ref to a far-down button, which it clicks directly. Agents
   recovered every time (JS scroll, then click), but in the wrong-row run the recovery clicked the wrong ref.

**Other full3 observations:** no request crossed the 100K-token price tier; 1 provider stall (gpt-6-luna,
~291 s with no tool running) was re-queued and rerun; full3 cost $0.83 (Haiku $0.06, glm $0.09, luna $0.04,
sol $0.63).

**Caveat:** like cloak-mcp v2, this change was designed after seeing v1's large-page results and targets the
weakness this suite exposed; it was not tuned on the suite's fixtures, and the suite, checkers and prompts are
unchanged. The full -> full2 drift of the unchanged Kairos (Haiku: +11% tokens per success overall, +23% on large
pages, -3 points success) is the noise band to read the v2 changes against: the large-page drop (-58% to -66%) is
far outside it, the small-category changes are inside it.
