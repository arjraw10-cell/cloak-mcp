# Kairos browser tools: v1 vs v2

v1 = Kairos ac28cd7 (phases `full` and `full2`, the same code run twice: their difference is the noise band);
v2 = Kairos 116efbc (phase `full3`, Kairos configs only): large-page card, `browser_search_page` over a fresh
accessibility snapshot with refs and context, `browser_snapshot` target/depth. Same 30 tasks, checkers, prompts,
limits and seeded run order.

Static schema (Anthropic tokens): Kairos v1 3,001, v2 3,117 (20 tools in both).

## claude-haiku-5-5

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | v1 (full) | 60 | 100% (94-100) | 0 | 0.18 | 35,580 | 4.6 | 0.0013 |
| all | v1 (full2) | 60 | 97% (89-99) | 0 | 0.32 | 39,384 | 4.8 | 0.0014 |
| all | v2 (full3) | 60 | 98% (91-100) | 0 | 0.23 | 26,140 | 4.1 | 0.0010 |
| basic | v1 (full) | 12 | 100% (76-100) | 0 | 0.00 | 20,498 | 2.5 | 0.0010 |
| basic | v1 (full2) | 12 | 92% (65-99) | 0 | 0.00 | 20,198 | 2.4 | 0.0009 |
| basic | v2 (full3) | 12 | 100% (76-100) | 0 | 0.00 | 19,780 | 2.3 | 0.0009 |
| forms | v1 (full) | 10 | 100% (72-100) | 0 | 0.40 | 33,348 | 5.6 | 0.0012 |
| forms | v1 (full2) | 10 | 100% (72-100) | 0 | 0.50 | 32,263 | 5.2 | 0.0012 |
| forms | v2 (full3) | 10 | 100% (72-100) | 0 | 0.60 | 34,925 | 5.6 | 0.0013 |
| dialogs | v1 (full) | 10 | 100% (72-100) | 0 | 0.40 | 27,475 | 5.5 | 0.0009 |
| dialogs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.50 | 27,156 | 5.5 | 0.0009 |
| dialogs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.50 | 27,126 | 5.2 | 0.0009 |
| frames-tabs | v1 (full) | 10 | 100% (72-100) | 0 | 0.00 | 17,607 | 3.6 | 0.0008 |
| frames-tabs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.00 | 17,473 | 3.4 | 0.0008 |
| frames-tabs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.00 | 18,050 | 3.5 | 0.0007 |
| large | v1 (full) | 10 | 100% (72-100) | 0 | 0.10 | 94,248 | 6.7 | 0.0030 |
| large | v1 (full2) | 10 | 100% (72-100) | 0 | 0.70 | 115,598 | 8.1 | 0.0036 |
| large | v2 (full3) | 10 | 90% (60-98) | 0 | 0.20 | 39,213 | 5.0 | 0.0017 |
| dynamic | v1 (full) | 8 | 100% (68-100) | 0 | 0.25 | 20,258 | 4.1 | 0.0009 |
| dynamic | v1 (full2) | 8 | 88% (53-98) | 0 | 0.25 | 19,601 | 4.8 | 0.0011 |
| dynamic | v2 (full3) | 8 | 100% (68-100) | 0 | 0.12 | 18,871 | 3.1 | 0.0008 |

## glm-5.3-flash

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | v1 (full) | 60 | 95% (86-98) | 0 | 0.12 | 20,446 | 4.1 | 0.0022 |
| all | v1 (full2) | 60 | 95% (86-98) | 0 | 0.15 | 23,650 | 3.7 | 0.0020 |
| all | v2 (full3) | 60 | 100% (94-100) | 0 | 0.15 | 22,020 | 3.6 | 0.0015 |
| basic | v1 (full) | 12 | 92% (65-99) | 0 | 0.00 | 13,602 | 2.1 | 0.0013 |
| basic | v1 (full2) | 12 | 92% (65-99) | 0 | 0.00 | 12,872 | 2.1 | 0.0011 |
| basic | v2 (full3) | 12 | 100% (76-100) | 0 | 0.00 | 15,441 | 2.5 | 0.0012 |
| forms | v1 (full) | 10 | 100% (72-100) | 0 | 0.60 | 20,976 | 4.0 | 0.0016 |
| forms | v1 (full2) | 10 | 100% (72-100) | 0 | 0.60 | 21,848 | 4.2 | 0.0020 |
| forms | v2 (full3) | 10 | 100% (72-100) | 0 | 0.50 | 22,460 | 4.3 | 0.0016 |
| dialogs | v1 (full) | 10 | 100% (72-100) | 0 | 0.00 | 19,798 | 4.2 | 0.0012 |
| dialogs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.10 | 18,903 | 4.0 | 0.0012 |
| dialogs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.20 | 19,485 | 4.1 | 0.0013 |
| frames-tabs | v1 (full) | 10 | 100% (72-100) | 0 | 0.00 | 13,456 | 2.6 | 0.0011 |
| frames-tabs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.00 | 14,301 | 2.8 | 0.0010 |
| frames-tabs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.00 | 13,914 | 2.6 | 0.0013 |
| large | v1 (full) | 10 | 80% (49-94) | 0 | 0.10 | 44,377 | 9.2 | 0.0068 |
| large | v1 (full2) | 10 | 90% (60-98) | 0 | 0.20 | 63,163 | 6.9 | 0.0055 |
| large | v2 (full3) | 10 | 100% (72-100) | 0 | 0.20 | 46,430 | 5.6 | 0.0026 |
| dynamic | v1 (full) | 8 | 100% (68-100) | 0 | 0.00 | 14,808 | 2.6 | 0.0013 |
| dynamic | v1 (full2) | 8 | 88% (53-98) | 0 | 0.00 | 12,495 | 2.2 | 0.0011 |
| dynamic | v2 (full3) | 8 | 100% (68-100) | 0 | 0.00 | 14,130 | 2.5 | 0.0012 |

## gpt-6-luna

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | v1 (full) | 60 | 92% (82-96) | 0 | 0.22 | 19,213 | 3.5 | 0.0007 |
| all | v1 (full2) | 60 | 95% (86-98) | 0 | 0.22 | 17,377 | 3.4 | 0.0007 |
| all | v2 (full3) | 60 | 92% (82-96) | 0 | 0.15 | 16,797 | 3.6 | 0.0007 |
| basic | v1 (full) | 12 | 83% (55-95) | 0 | 0.00 | 12,539 | 2.4 | 0.0007 |
| basic | v1 (full2) | 12 | 83% (55-95) | 0 | 0.00 | 11,840 | 2.4 | 0.0007 |
| basic | v2 (full3) | 12 | 83% (55-95) | 0 | 0.00 | 13,521 | 2.9 | 0.0008 |
| forms | v1 (full) | 10 | 100% (72-100) | 0 | 0.40 | 16,849 | 4.2 | 0.0006 |
| forms | v1 (full2) | 10 | 100% (72-100) | 0 | 0.40 | 16,766 | 4.1 | 0.0006 |
| forms | v2 (full3) | 10 | 100% (72-100) | 0 | 0.30 | 17,729 | 4.5 | 0.0006 |
| dialogs | v1 (full) | 10 | 100% (72-100) | 0 | 0.20 | 14,872 | 4.0 | 0.0005 |
| dialogs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.20 | 14,533 | 3.9 | 0.0005 |
| dialogs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.20 | 15,424 | 4.0 | 0.0005 |
| frames-tabs | v1 (full) | 10 | 100% (72-100) | 0 | 0.00 | 10,903 | 2.7 | 0.0004 |
| frames-tabs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.00 | 11,221 | 2.8 | 0.0004 |
| frames-tabs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.00 | 10,945 | 2.6 | 0.0004 |
| large | v1 (full) | 10 | 90% (60-98) | 0 | 0.60 | 47,750 | 4.8 | 0.0015 |
| large | v1 (full2) | 10 | 100% (72-100) | 0 | 0.50 | 37,124 | 4.0 | 0.0013 |
| large | v2 (full3) | 10 | 90% (60-98) | 0 | 0.30 | 32,530 | 5.0 | 0.0011 |
| dynamic | v1 (full) | 8 | 75% (41-93) | 0 | 0.12 | 12,558 | 3.4 | 0.0006 |
| dynamic | v1 (full2) | 8 | 88% (53-98) | 0 | 0.25 | 10,805 | 3.0 | 0.0006 |
| dynamic | v2 (full3) | 8 | 75% (41-93) | 0 | 0.12 | 9,149 | 2.6 | 0.0006 |

## gpt-6.1-sol

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | v1 (full) | 60 | 98% (91-100) | 0 | 0.23 | 18,286 | 3.5 | 0.0122 |
| all | v1 (full2) | 60 | 97% (89-99) | 0 | 0.30 | 19,153 | 3.4 | 0.0123 |
| all | v2 (full3) | 60 | 97% (89-99) | 0 | 0.15 | 15,229 | 3.3 | 0.0106 |
| basic | v1 (full) | 12 | 100% (76-100) | 0 | 0.25 | 17,093 | 2.8 | 0.0129 |
| basic | v1 (full2) | 12 | 100% (76-100) | 0 | 0.25 | 18,558 | 2.8 | 0.0137 |
| basic | v2 (full3) | 12 | 100% (76-100) | 0 | 0.00 | 14,328 | 2.7 | 0.0115 |
| forms | v1 (full) | 10 | 100% (72-100) | 0 | 0.50 | 17,414 | 4.2 | 0.0110 |
| forms | v1 (full2) | 10 | 100% (72-100) | 0 | 0.40 | 16,667 | 4.0 | 0.0108 |
| forms | v2 (full3) | 10 | 100% (72-100) | 0 | 0.40 | 17,220 | 4.0 | 0.0111 |
| dialogs | v1 (full) | 10 | 90% (60-98) | 0 | 0.20 | 16,792 | 4.4 | 0.0095 |
| dialogs | v1 (full2) | 10 | 80% (49-94) | 0 | 0.10 | 15,606 | 4.0 | 0.0091 |
| dialogs | v2 (full3) | 10 | 80% (49-94) | 0 | 0.20 | 17,545 | 4.3 | 0.0097 |
| frames-tabs | v1 (full) | 10 | 100% (72-100) | 0 | 0.00 | 10,911 | 2.7 | 0.0081 |
| frames-tabs | v1 (full2) | 10 | 100% (72-100) | 0 | 0.00 | 11,231 | 2.8 | 0.0082 |
| frames-tabs | v2 (full3) | 10 | 100% (72-100) | 0 | 0.00 | 11,624 | 2.8 | 0.0084 |
| large | v1 (full) | 10 | 100% (72-100) | 0 | 0.20 | 34,274 | 3.9 | 0.0217 |
| large | v1 (full2) | 10 | 100% (72-100) | 0 | 0.80 | 38,701 | 4.1 | 0.0224 |
| large | v2 (full3) | 10 | 100% (72-100) | 0 | 0.20 | 19,031 | 3.4 | 0.0127 |
| dynamic | v1 (full) | 8 | 100% (68-100) | 0 | 0.25 | 12,078 | 2.8 | 0.0095 |
| dynamic | v1 (full2) | 8 | 100% (68-100) | 0 | 0.25 | 12,166 | 2.8 | 0.0086 |
| dynamic | v2 (full3) | 8 | 100% (68-100) | 0 | 0.12 | 11,526 | 2.4 | 0.0097 |

## Large-page tasks: mean tokens (in + out) per run, and passes (Haiku 5.5)

| task | Kairos full | Kairos full2 | Kairos full3 | cloak-mcp v2 (full2, reference) |
|---|---|---|---|---|
| large-archive | 179,946 (2/2) | 268,422 (2/2) | 96,664 (1/2) | 56,086 (2/2) |
| large-article | 22,830 (2/2) | 45,772 (2/2) | 30,681 (2/2) | 17,840 (2/2) |
| large-country | 184,372 (2/2) | 176,220 (2/2) | 54,214 (2/2) | 34,058 (2/2) |
| large-order-count | 35,088 (2/2) | 43,155 (2/2) | 27,282 (2/2) | 46,686 (2/2) |
| large-order-status | 49,003 (2/2) | 44,423 (2/2) | 22,143 (2/2) | 11,312 (2/2) |

## How Kairos agents used page search and section snapshots (all models)

| run | tool | calls | runs using it | of which Haiku | mean result tokens | max result tokens |
|---|---|---|---|---|---|---|
| v1 (full) | browser_search_page | 35 | 28 | 14 | 67 | 340 |
| v1 (full) | browser_snapshot (target/depth) | 0 | 0 | 0 | - | - |
| v1 (full) | browser_snapshot (whole page) | 62 | 47 | 32 | 923 | 5,383 |
| v1 (full2) | browser_search_page | 39 | 33 | 14 | 70 | 194 |
| v1 (full2) | browser_snapshot (target/depth) | 0 | 0 | 0 | - | - |
| v1 (full2) | browser_snapshot (whole page) | 45 | 34 | 22 | 696 | 5,382 |
| v2 (full3) | browser_search_page | 52 | 39 | 15 | 454 | 6,425 |
| v2 (full3) | browser_snapshot (target/depth) | 32 | 25 | 2 | 888 | 5,662 |
| v2 (full3) | browser_snapshot (whole page) | 25 | 19 | 22 | 168 | 494 |

`browser_navigate` result size on large-page tasks (all models): v1 (full) mean 4,498 tokens (max 5,940); v1 (full2) mean 4,711 tokens (max 5,940); v2 (full3) mean 1,395 tokens (max 1,792).

## Slow or timed-out clicks (known humanized-scroll issue)

- `full2.kairos.glm-5.3-flash.large-archive.r2` call 4: latency 12.353 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full2.kairos.claude-haiku-5-5.large-country.r2` call 9: latency 10.021 s, error: Click failed: Locator.element_handle: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: ht
- `full2.kairos.glm-5.3-flash.large-archive.r1` call 16: latency 12.428 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.gpt-6-luna.large-archive.r2` call 3: latency 12.423 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.gpt-6.1-sol.large-archive.r1` call 4: latency 12.41 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.claude-haiku-5-5.large-archive.r2` call 3: latency 12.602 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.claude-haiku-5-5.large-archive.r1` call 3: latency 12.419 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.glm-5.3-flash.large-archive.r2` call 3: latency 12.42 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.gpt-6-luna.large-archive.r1` call 4: latency 12.546 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.gpt-6.1-sol.large-archive.r2` call 4: latency 12.389 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
- `full3.kairos.glm-5.3-flash.large-archive.r1` call 3: latency 12.373 s, error: Click failed: ElementHandle.click: Timeout 10000ms exceeded. The element may be hidden, covered, or not rendered yet; check the snapshot below.

Page URL: http:
