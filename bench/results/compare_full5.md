# Kairos across the reruns

Same 30 tasks, checkers, fixtures, prompts, limits and seeded run order in every phase. Kairos versions:
`full` and `full2` = v1 ac28cd7 (the same code run twice: their difference is the noise band), `full3` = v2
116efbc, `full4` = v2.1 0367e99, `full5` = f1ff3f8 (adds 328f1a3: `browser_console` refuses while a dialog is
open; 0310529/a9820da: `browser_type` retypes once without CloakBrowser's typos when stray letters are left).
Large-page tokens = mean tokens (in + out) per run over the 5 large-page tasks.

## claude-haiku-5-5

| run | runs | success (95% CI) | hangs | tool errors/run | tokens/success | large-page tokens/run | calls/task |
|---|---|---|---|---|---|---|---|
| full (v1) | 60 | 100% (94-100) | 0 | 0.18 | 35,580 | 94,248 | 4.6 |
| full2 (v1 rerun) | 60 | 97% (89-99) | 0 | 0.32 | 39,384 | 115,598 | 4.8 |
| full3 (v2) | 60 | 98% (91-100) | 0 | 0.23 | 26,140 | 46,197 | 4.1 |
| full4 (v2.1) | 60 | 93% (84-97) | 0 | 0.23 | 27,800 | 44,583 | 4.2 |
| full5 (f1ff3f8) | 60 | 98% (91-100) | 0 | 0.18 | 27,362 | 44,645 | 4.2 |

## glm-5.3-flash

| run | runs | success (95% CI) | hangs | tool errors/run | tokens/success | large-page tokens/run | calls/task |
|---|---|---|---|---|---|---|---|
| full (v1) | 60 | 95% (86-98) | 0 | 0.12 | 20,446 | 150,191 | 4.1 |
| full2 (v1 rerun) | 60 | 95% (86-98) | 0 | 0.15 | 23,650 | 97,660 | 3.7 |
| full3 (v2) | 60 | 100% (94-100) | 0 | 0.15 | 22,020 | 46,430 | 3.6 |
| full4 (v2.1) | 60 | 98% (91-100) | 0 | 0.13 | 20,234 | 33,303 | 3.5 |
| full5 (f1ff3f8) | 60 | 98% (91-100) | 0 | 0.18 | 23,164 | 45,399 | 3.8 |

## gpt-6-luna

| run | runs | success (95% CI) | hangs | tool errors/run | tokens/success | large-page tokens/run | calls/task |
|---|---|---|---|---|---|---|---|
| full (v1) | 60 | 92% (82-96) | 0 | 0.22 | 19,213 | 49,568 | 3.5 |
| full2 (v1 rerun) | 60 | 95% (86-98) | 0 | 0.22 | 17,377 | 37,124 | 3.4 |
| full3 (v2) | 60 | 92% (82-96) | 0 | 0.15 | 16,797 | 33,927 | 3.6 |
| full4 (v2.1) | 60 | 93% (84-97) | 0 | 0.15 | 14,444 | 16,111 | 3.3 |
| full5 (f1ff3f8) | 60 | 95% (86-98) | 0 | 0.10 | 14,633 | 15,666 | 3.3 |

## gpt-6.1-sol

| run | runs | success (95% CI) | hangs | tool errors/run | tokens/success | large-page tokens/run | calls/task |
|---|---|---|---|---|---|---|---|
| full (v1) | 60 | 98% (91-100) | 0 | 0.23 | 18,286 | 34,274 | 3.5 |
| full2 (v1 rerun) | 60 | 97% (89-99) | 0 | 0.30 | 19,153 | 38,701 | 3.4 |
| full3 (v2) | 60 | 97% (89-99) | 0 | 0.15 | 15,229 | 19,031 | 3.3 |
| full4 (v2.1) | 60 | 97% (89-99) | 0 | 0.18 | 15,309 | 17,399 | 3.3 |
| full5 (f1ff3f8) | 60 | 97% (89-99) | 0 | 0.13 | 14,854 | 16,999 | 3.2 |

## Per category, claude-haiku-5-5 (tokens per success)

| category | full | full2 | full3 | full4 | full5 |
|---|---|---|---|---|---|
| basic | 20,498 (100%) | 20,198 (92%) | 19,780 (100%) | 19,433 (83%) | 21,417 (92%) |
| forms | 33,348 (100%) | 32,263 (100%) | 34,925 (100%) | 35,476 (100%) | 33,546 (100%) |
| dialogs | 27,475 (100%) | 27,156 (100%) | 27,126 (100%) | 26,775 (90%) | 27,252 (100%) |
| frames-tabs | 17,607 (100%) | 17,473 (100%) | 18,050 (100%) | 18,052 (100%) | 17,957 (100%) |
| large | 94,248 (100%) | 115,598 (100%) | 39,213 (90%) | 44,583 (100%) | 44,645 (100%) |
| dynamic | 20,258 (100%) | 19,601 (88%) | 18,871 (100%) | 20,056 (88%) | 18,095 (100%) |

## dyn-spa-create: created names and browser_type latency (all models)

| run | runs | runs with a name other than "Orion" | browser_type calls | median latency s | max latency s |
|---|---|---|---|---|---|
| full (v1) | 8 | 1 | 7 | 3.6 | 4.1 |
| full2 (v1 rerun) | 8 | 1 | 9 | 3.8 | 5.3 |
| full3 (v2) | 8 | 0 | 8 | 4.1 | 5.3 |
| full4 (v2.1) | 8 | 1 | 8 | 4.3 | 4.6 |
| full5 (f1ff3f8) | 8 | 0 | 8 | 4.0 | 6.7 |

- full: `full.kairos.gpt-6-luna.dyn-spa-create.r2` created ['Oriomn']
- full2: `full2.kairos.claude-haiku-5-5.dyn-spa-create.r2` created ['Orilon', 'Orion']
- full4: `full4.kairos.claude-haiku-5-5.dyn-spa-create.r1` created ['Orkion']

## dialogs-welcome: browser_console while the alert is open, and silent exits (all models)

- full (v1): 8 runs, 8 passed, 2 browser_console calls, 0 calls that never returned, 0 runs ending in status error
  - console: `full.kairos.claude-haiku-5-5.dialogs-welcome.r1`: 'Console failed: Browser operation timed out after 120s.'
  - console: `full.kairos.gpt-6.1-sol.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
- full2 (v1 rerun): 8 runs, 8 passed, 1 browser_console calls, 0 calls that never returned, 0 runs ending in status error
  - console: `full2.kairos.claude-haiku-5-5.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
- full3 (v2): 8 runs, 8 passed, 3 browser_console calls, 0 calls that never returned, 0 runs ending in status error
  - console: `full3.kairos.glm-5.3-flash.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
  - console: `full3.kairos.claude-haiku-5-5.dialogs-welcome.r1`: 'Console failed: Browser operation timed out after 120s.'
  - console: `full3.kairos.claude-haiku-5-5.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
- full4 (v2.1): 8 runs, 7 passed, 3 browser_console calls, 1 calls that never returned, 1 runs ending in status error (exit codes [None])
  - console: `full4.kairos.glm-5.3-flash.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
  - console: `full4.kairos.claude-haiku-5-5.dialogs-welcome.r1`: 'Console failed: Browser operation timed out after 120s.'
  - console: `full4.kairos.gpt-6.1-sol.dialogs-welcome.r2`: 'Console failed: Browser operation timed out after 120s.'
  - never returned: `full4.kairos.claude-haiku-5-5.dialogs-welcome.r2` call 3 browser_console
- full5 (f1ff3f8): 8 runs, 8 passed, 4 browser_console calls, 0 calls that never returned, 0 runs ending in status error
  - console: `full5.kairos.glm-5.3-flash.dialogs-welcome.r2`: 'Console failed: A alert dialog is open ("Welcome! Your access code is ZK-73."). Call browser_handle_dialog first.'
  - console: `full5.kairos.claude-haiku-5-5.dialogs-welcome.r1`: 'Console failed: A alert dialog is open ("Welcome! Your access code is ZK-73."). Call browser_handle_dialog first.'
  - console: `full5.kairos.gpt-6.1-sol.dialogs-welcome.r2`: 'Console failed: A alert dialog is open ("Welcome! Your access code is ZK-73."). Call browser_handle_dialog first.'
  - console: `full5.kairos.glm-5.3-flash.dialogs-welcome.r1`: 'Console failed: A alert dialog is open ("Welcome! Your access code is ZK-73."). Call browser_handle_dialog first.'

## full5 child-process exit codes

- {0: 240} (status error: none)

## Every full5 failure

- `full5.kairos.claude-haiku-5-5.pub-quotes-author.r1`: done, exit code 0, answer 'July 12, 1904 in Parral, Chile'
- `full5.kairos.glm-5.3-flash.pub-quotes-author.r1`: done, exit code 0, answer 'July 12, 1904 in Parral, Chile'
- `full5.kairos.gpt-6-luna.pub-quotes-author.r1`: done, exit code 0, answer 'July 12, 1904 in Parral, Chile'
- `full5.kairos.gpt-6-luna.pub-quotes-author.r2`: done, exit code 0, answer 'July 12, 1904 in Parral, Chile'
- `full5.kairos.gpt-6-luna.pub-quotes-scroll.r1`: done, exit code 0, answer 'Albert Einstein'
- `full5.kairos.gpt-6.1-sol.pub-js-prompt.r1`: done, exit code 0, answer 'done'
- `full5.kairos.gpt-6.1-sol.pub-js-prompt.r2`: done, exit code 0, answer 'done'
