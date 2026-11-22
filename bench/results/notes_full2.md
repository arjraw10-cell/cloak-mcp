## Findings for full2 (cloak-mcp v2 = 76211fc; written after the run, tables below are generated)

full2 reruns the identical v1 suite (same 30 tasks, checkers, fixtures, prompts, limits, seeded run order) with
every config; only cloak-mcp changed (96aa864 -> 76211fc). The full v1 vs v2 tables are in `compare_v1_v2.md`.

**cloak-mcp v1 -> v2 (Claude Code + Haiku 5.5, 60 runs each):**

- Success 97% -> 100% (58/60 -> 60/60). The two v1 misses (`pub-quotes-author`, which copied "July 12, 1904 in
  Parral, Chile") passed in v2: the agent ran `browser_find "Born"` on the author page instead of reading the merged
  snapshot line. One task, two runs: treat it as a small, plausible gain, not a proven one.
- Hangs 0 -> 0. Tool errors per run 0.07 -> 0.05.
- Tokens per successful task, all categories: 35.8k -> 22.5k (-37%). Large pages: 117k -> 33k (-72%), now the lowest
  of the four core configs on large pages (v2 run: Playwright MCP ~46k, devinwangd ~91k, Kairos ~116k per run on
  average across the 5 large tasks). `browser_navigate` results on large pages: mean 8.9k -> 1.3k tokens.
- Tool calls per task 4.5 -> 4.9.
- Small categories (basic, forms, dialogs, frames-tabs, dynamic): tokens per success up 4-14% and +0.2 to +0.8
  calls per task. Two causes: (1) the schema grew by 385 tokens (20 -> 21 tools), sent on every request, which is
  about +2k tokens on a 5-request run and accounts for most of the basic (+2.2k) and frames-tabs (+2.4k) increase;
  (2) agents now also call `browser_find` on small pages (14 of its 33 calls were on basic tasks), adding a call
  where reading the inline snapshot would do. Compare the noise baseline: the unchanged configs drifted -10% to +16%
  in tokens per success and up to +0.7 calls per task between the two runs, so this is a mild regression at most,
  slightly above noise only for basic and frames-tabs (+14%).

**Noise baseline (unchanged configs, v1 -> v2):** devinwangd 83% -> 82%, Playwright MCP 98% -> 100%, Kairos (Haiku)
100% -> 97%, glm 95% -> 95%, luna 92% -> 95%, sol 98% -> 97%. Success moved by up to 3 points and tokens per success
by -10% (luna) to +16% (glm) with no code change, so cloak-mcp's small-category changes are within that band and only the large
-page drop is far outside it.

**How v2 agents used the new tools (cc-cloak):** `browser_find` 33 calls in 22 of 60 runs (basic 14, large 12,
frames-tabs 4, dialogs 3), mean result 428 tokens, max 3,590 (a broad "£" search returning 20 matches with context).
`browser_snapshot` with target/depth: only 4 calls in 2 runs (both `large-archive`, reading one table row, ~110
tokens each). Whole-page `browser_snapshot` is still the agents' habit: 64 calls in 31 runs, mostly on small pages;
on large pages it was called 3 times, and the `large-country` runs got a 22k-character (10.7k-token) result from it.

**Where v2 did not help or could mislead (no cloak-mcp v2 run failed, and no cloak-mcp bug was found):**

1. `full2.cc-cloak.claude-haiku-5-5.large-country.r1`: the agent issued `browser_navigate` and a whole-page
   `browser_snapshot` in the same turn, so the card was bypassed and the full 22k-character snapshot came back
   anyway (34k tokens per run vs 47k in v1, a smaller saving than elsewhere). The card's outline listed only the two
   headings; it does not mention forms or the `<select>`, so on its own it would not have shown the agent where the
   control was.
2. `full2.cc-cloak.claude-haiku-5-5.basic-faq.r1`: `browser_find "canada"` returned "No matches" because the answer
   sits inside a collapsed `<details>` section, which the snapshot does not include. The agent opened the section and
   searched again; a less careful agent could read "No matches" as "not on the page".
3. `full2.cc-cloak.claude-haiku-5-5.large-archive.r1`: the biggest win (56k tokens per run vs 386k in v1). The card
   (4.6k characters instead of ~30k), then `browser_find "T-0842"`, then `browser_snapshot target=e2656` (267
   characters) to read the row. The agent still reloaded the page to verify the archive (the fixture keeps the row,
   see the v1 notes), but each reload now cost ~1.1k tokens instead of ~10k.
   Also worth noting: on `large-order-count` cloak-mcp v2 (46.7k) is still behind Playwright MCP (40.7k) and Kairos
   (43.2k).

**Other full2 observations:**

- No request crossed the Haiku 100K-token price tier (0 runs in any config).
- 5 provider stalls, all gpt-6.1-sol (~290 s waiting on the API with no tool running), were logged in
  `api_errors.jsonl`, re-queued and rerun; nothing was left unrun. Retries reuse the run's transcript and `.err` file
  names, so the stack dumps of stalled attempts were overwritten by the successful retry.
- Kairos (Haiku) failed `dyn-spa-create` once by first creating "Orilon" then "Orion" (the same late-applying-input
  weakness gpt-6-luna showed in v1), and `pub-quotes-author` once (birthplace included).
- devinwangd again froze on every dialog task (10/10 timeouts).

**Caveat:** the v2 change was designed after seeing v1's large-page results, so it targets exactly the weakness
this suite exposed, and the large-page gain should be read with that in mind. It was not tuned on the suite's
fixtures (the author tested it on a separate 1,500-row page that is not in the suite), and the suite, checkers and
prompts were not changed. An independent large-page test set would make the claim stronger.
