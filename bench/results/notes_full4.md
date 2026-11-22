## Findings for full4 (cloak-mcp v2.1 = 1d22924, Kairos v2.1 = 0367e99; written after the run, tables below are generated)

full4 reruns the identical suite (same 30 tasks, checkers, fixtures, prompts, limits; v1's seeded order, filtered)
for cc-cloak and the four Kairos configs, after fixes for the three problems found in full3. Full tables across all
phases: `compare_full4.md`. Static schemas are unchanged from v2 (cloak-mcp 21 tools / 3,764 tokens, Kairos 20
tools / 3,117): the fixes changed behavior, not tool descriptions.

**The three full3 problems: fixed.**

1. *Wrong-row actions.* 0 in full4 (full3: 1, Kairos-Haiku archived T-0841). All 10 `large-archive` runs (cc-cloak
   and every Kairos model) archived the right ticket. The search result now shows the matched row with its own
   button, e.g. `row [ref=e2656]: ... button "Archive" [ref=e2661]`, and no longer the previous row's.
   The one remaining wrong-value action in full4 is `full4.kairos.claude-haiku-5-5.dyn-spa-create.r1` (created
   "Orkion" instead of "Orion"), the pre-existing late-applying-input typing problem also seen in full (gpt-6-luna,
   "Oriomn") and full2 (Haiku, "Orilon"); it is unrelated to these fixes.
2. *Literal "a|b" searches.* Kairos: 6 such searches in full4, all rescued by the new fallback (full3: 0 of 9
   rescued; full and full2 with v1 code: 0 of 7 each, so this was a v1 problem too, not one v2 introduced). cloak-mcp
   agents wrote no literal "|" searches in full2 or full4 (their one "|" search was a real regex).
3. *Click timeouts on far-down refs.* 0 in full4 (full3: 8, every `large-archive` run); no Kairos click took over
   10 s. Kairos-Haiku's clicks on the Archive button ~3,600 px down took 3.0-3.1 s. cloak-mcp's two slow clicks in full4 (and two in every earlier
   phase) are a different, pre-existing behavior: after switching tabs on `tabs-coupon`, the next click on the
   original tab takes ~30 s (it succeeds).

**cloak-mcp, v1 full / v2 full2 -> v2.1 full4 (60 runs each):** success 97% / 100% -> 97%; hangs 0; tool errors per
run 0.07 / 0.05 -> 0.07; tokens per success 35.8k / 22.5k -> 22.8k; calls per task 4.5 / 4.9 -> 5.2. Large pages:
117k / 33k -> 31k per success; mean over the 5 large tasks 30.5k per run vs 45.5k for Playwright MCP (full2).
`large-order-count` fell from 47k to 21k. The two failures: `pub-quotes-author.r2` (birthplace included, as in v1)
and `pub-books-price.r2`, a new one (below).

**Kairos on Haiku, v1 full / v1 full2 / v2 full3 -> v2.1 full4:** success 100% / 97% / 98% -> 93%; hangs 0; tool
errors per run 0.18 / 0.32 / 0.23 -> 0.23; tokens per success 35.6k / 39.4k / 26.1k -> 27.8k; calls per task 4.6 /
4.8 / 4.1 -> 4.2; large pages 94k / 116k / 39k -> 45k per success (mean over the 5 tasks per run 94k / 116k / 46k ->
45k). The four failures: `pub-quotes-author` x2 (checker strictness, birthplace included), `dyn-spa-create.r1`
(late-input typing, above) and `dialogs-welcome.r2` (silent exit, below). None is caused by the large-page fixes,
but the 93% is the lowest Kairos-Haiku rate so far; with 60 runs the 95% interval is 84-97%, overlapping every
earlier run.

**Kairos bonus models, full3 -> full4:** glm-5.3-flash 100% -> 98%, 22.0k -> 20.2k tokens per success (large 46k ->
33k); gpt-6-luna 92% -> 93%, 16.8k -> 14.4k (large 33k -> 16k, large success 90% -> 100%, the `large-country`
failure from full3 is gone); gpt-6.1-sol 97% -> 97%, 15.2k -> 15.3k (large 19k -> 17k).

**Small categories vs the noise band (unchanged Kairos v1, full -> full2: -10% to +16% in tokens per success):**
cc-cloak full2 -> full4: basic -7%, dialogs 0%, frames-tabs -3%, dynamic +1%, forms +19%; the forms rise is one
outlier, `full4.cc-cloak.claude-haiku-5-5.forms-booking.r2` (25 calls, 93k tokens fighting the date field); every
other forms run was token-for-token identical to full2. Kairos-Haiku full3 -> full4: basic -2%, forms +2%,
dialogs -1%, frames-tabs 0%, dynamic +6%. No small-category regression.

**New failure modes and surprises:**

- `full4.cc-cloak.claude-haiku-5-5.pub-books-price.r2` (new): the agent ran a broad `browser_find "£"`; with whole
  list items as context the result was 21.7k characters (14.4k in full2), listing every book in order with its price.
  The agent wrote out the right order ("In Her Wake, How Music Works, Foolproof Preserving, then Chase Me") and then
  called the 4th book the 3rd (answered £25.27, not £30.52). The output was correct; the model miscounted. One run,
  so weak evidence that the larger whole-item context hurts broad searches.
- `full4.kairos.claude-haiku-5-5.dialogs-welcome.r2` (new): the Kairos process exited silently ~15 s in, while a
  `browser_console` call was running with the page's `alert()` open; no traceback, no final record (the harness does
  not record the child's exit code). A no-LLM repro of the same sequence did not crash, but `browser_console` with an
  open alert blocked for the full 120 s browser-operation timeout 3 times out of 3 (pre-existing: the same "Console
  failed: Browser operation timed out after 120s" error appears in v1's `full` run). Root cause of the exit unknown.
- `full4.kairos.claude-haiku-5-5.large-article.r1`: the "a|b" fallback rescued `"rebuil|Harrow Point"`, but the
  result was ~10k characters, since each part matches many lines on a long article. Rescued searches can be broad.
- Search use (full4): cloak-mcp `browser_find` 35 calls in 21 runs (mean 398 result tokens, max 5,258); Kairos
  `browser_search_page` 52 calls in 43 runs (mean 409, max 3,109); Kairos section snapshots 23 calls, mean 216 tokens
  (820 in full3). cloak-mcp agents did not use `browser_snapshot` target/depth at all in full4. (Result tokens here
  are counted on the result text; `compare_kairos.md` counted Kairos's JSON-wrapped result, so its numbers are ~10%
  higher.)
- No request crossed the 100K-token price tier; no provider stalls in full4. full4 cost $0.88 (cc-cloak $0.05, Kairos
  Haiku $0.06, glm $0.09, luna $0.04, sol $0.64).

**Caveat:** these fixes were designed after seeing the full3 failures on this exact suite (the wrong-row archive on
`large-archive`, the "|" misses on `large-article` / `large-country`, the click timeouts on `large-archive`), so
full4 confirms that they fix those cases, not that they generalize. They were not tuned on the fixtures beyond that,
and the suite, checkers and prompts are unchanged. A held-out large-page test set would be the honest next check.
