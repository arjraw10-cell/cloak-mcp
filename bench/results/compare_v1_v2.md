# cloak-mcp v1 vs v2

v1 = phase `full` (cloak-mcp 96aa864), v2 = phase `full2` (cloak-mcp 76211fc). Same 30 tasks, checkers, prompts,
limits and run order; every config was rerun, so the unchanged configs give a same-setup noise baseline.

Static schema: cloak-mcp v1 20 tools / 3,379 tokens, v2 21 tools / 3,764 tokens (Anthropic count).

## cc-cloak, overall and per category

| scope | version | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | v1 | 60 | 97% (89-99) | 0 | 0.07 | 35,822 | 4.5 | 0.0014 |
| all | v2 | 60 | 100% (94-100) | 0 | 0.05 | 22,482 | 4.9 | 0.0009 |
| basic | v1 | 12 | 83% (55-95) | 0 | 0.00 | 15,771 | 2.6 | 0.0008 |
| basic | v2 | 12 | 100% (76-100) | 0 | 0.00 | 17,927 | 3.4 | 0.0008 |
| forms | v1 | 10 | 100% (72-100) | 0 | 0.00 | 27,339 | 6.5 | 0.0010 |
| forms | v2 | 10 | 100% (72-100) | 0 | 0.00 | 28,310 | 7.0 | 0.0010 |
| dialogs | v1 | 10 | 100% (72-100) | 0 | 0.30 | 21,191 | 5.3 | 0.0007 |
| dialogs | v2 | 10 | 100% (72-100) | 0 | 0.30 | 22,412 | 6.0 | 0.0007 |
| frames-tabs | v1 | 10 | 100% (72-100) | 0 | 0.00 | 16,980 | 4.9 | 0.0006 |
| frames-tabs | v2 | 10 | 100% (72-100) | 0 | 0.00 | 19,336 | 5.6 | 0.0006 |
| large | v1 | 10 | 100% (72-100) | 0 | 0.10 | 117,223 | 5.0 | 0.0047 |
| large | v2 | 10 | 100% (72-100) | 0 | 0.00 | 33,196 | 4.1 | 0.0015 |
| dynamic | v1 | 8 | 100% (68-100) | 0 | 0.00 | 11,577 | 3.0 | 0.0005 |
| dynamic | v2 | 8 | 100% (68-100) | 0 | 0.00 | 12,657 | 3.2 | 0.0005 |

## Noise baseline: unchanged configs, v1 vs v2

| config / model | version | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| cc-devin / claude-haiku-5-5 | v1 | 60 | 83% (72-91) | 10 | 0.30 | 75,146 | 5.9 | 0.0014 |
| cc-devin / claude-haiku-5-5 | v2 | 60 | 82% (70-89) | 10 | 0.30 | 80,060 | 6.6 | 0.0015 |
| cc-playwright / claude-haiku-5-5 | v1 | 60 | 98% (91-100) | 1 | 0.25 | 38,625 | 5.8 | 0.0010 |
| cc-playwright / claude-haiku-5-5 | v2 | 60 | 100% (94-100) | 1 | 0.32 | 40,587 | 6.2 | 0.0011 |
| kairos / claude-haiku-5-5 | v1 | 60 | 100% (94-100) | 0 | 0.18 | 35,580 | 4.6 | 0.0013 |
| kairos / claude-haiku-5-5 | v2 | 60 | 97% (89-99) | 0 | 0.32 | 39,384 | 4.8 | 0.0014 |
| kairos / glm-5.3-flash | v1 | 60 | 95% (86-98) | 0 | 0.12 | 20,446 | 4.1 | 0.0022 |
| kairos / glm-5.3-flash | v2 | 60 | 95% (86-98) | 0 | 0.15 | 23,650 | 3.7 | 0.0020 |
| kairos / gpt-6-luna | v1 | 60 | 92% (82-96) | 0 | 0.22 | 19,213 | 3.5 | 0.0007 |
| kairos / gpt-6-luna | v2 | 60 | 95% (86-98) | 0 | 0.22 | 17,377 | 3.4 | 0.0007 |
| kairos / gpt-6.1-sol | v1 | 60 | 98% (91-100) | 0 | 0.23 | 18,286 | 3.5 | 0.0122 |
| kairos / gpt-6.1-sol | v2 | 60 | 97% (89-99) | 0 | 0.30 | 19,153 | 3.4 | 0.0123 |

## Large-page tasks: mean tokens (in + out) per run, and passes, core configs

| task | cc-cloak v1 | cc-cloak v2 | cc-devin v1 | cc-devin v2 | cc-playwright v1 | cc-playwright v2 | kairos v1 | kairos v2 |
|---|---|---|---|---|---|---|---|---|
| large-archive | 385,678 (2/2) | 56,086 (2/2) | 157,658 (2/2) | 189,277 (2/2) | 64,440 (2/2) | 89,600 (2/2) | 179,946 (2/2) | 268,422 (2/2) |
| large-article | 35,800 (2/2) | 17,840 (2/2) | 60,712 (2/2) | 61,998 (2/2) | 18,082 (2/2) | 18,084 (2/2) | 22,830 (2/2) | 45,772 (2/2) |
| large-country | 46,793 (2/2) | 34,058 (2/2) | 88,512 (2/2) | 89,062 (2/2) | 75,554 (2/2) | 58,599 (2/2) | 184,372 (2/2) | 176,220 (2/2) |
| large-order-count | 74,823 (2/2) | 46,686 (2/2) | 61,498 (2/2) | 61,348 (2/2) | 35,745 (2/2) | 40,698 (2/2) | 35,088 (2/2) | 43,155 (2/2) |
| large-order-status | 43,020 (2/2) | 11,312 (2/2) | 44,147 (2/2) | 52,450 (2/2) | 15,913 (2/2) | 20,516 (2/2) | 49,003 (2/2) | 44,423 (2/2) |

## How cc-cloak v2 agents used the new tools

| tool | calls | runs using it (of 60) | categories | mean result tokens | max result tokens |
|---|---|---|---|---|---|
| browser_find | 33 | 22 | basic 14, dialogs 3, frames-tabs 4, large 12 | 428 | 3,590 |
| browser_snapshot (target/depth) | 4 | 2 | large 4 | 110 | 111 |
| browser_snapshot (whole page) | 64 | 31 | basic 2, dialogs 16, dynamic 6, forms 23, frames-tabs 14, large 3 | 499 | 10,691 |

`browser_navigate` result size on large-page tasks: v1 mean 8,898 tokens (max 10,692), v2 mean 1,330 tokens (max 1,624).
