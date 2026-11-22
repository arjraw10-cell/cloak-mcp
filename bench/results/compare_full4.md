# cloak-mcp and Kairos across the reruns

Same 30 tasks, checkers, fixtures, prompts, limits and seeded run order in every phase (filtered phases keep the
full run's relative order). cloak-mcp: `full` = v1 96aa864, `full2` = v2 76211fc, `full4` = v2.1 1d22924.
Kairos: `full` and `full2` = v1 ac28cd7 run twice (their difference is the noise band), `full3` = v2 116efbc,
`full4` = v2.1 0367e99. All Claude Code rows use claude-haiku-5-5 at effort low.

Static schema (Anthropic tokens): cloak-mcp v1 3,379, v2 3,764, v2.1 3,764; Kairos v1 3,001, v2 3,117, v2.1 3,117.

## cloak-mcp (Claude Code, claude-haiku-5-5)

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | full (v1) | 60 | 97% (89-99) | 0 | 0.07 | 35,822 | 4.5 | 0.0014 |
| all | full2 (v2) | 60 | 100% (94-100) | 0 | 0.05 | 22,482 | 4.9 | 0.0009 |
| all | full4 (v2.1) | 60 | 97% (89-99) | 0 | 0.07 | 22,807 | 5.2 | 0.0009 |
| basic | full (v1) | 12 | 83% (55-95) | 0 | 0.00 | 15,771 | 2.6 | 0.0008 |
| basic | full2 (v2) | 12 | 100% (76-100) | 0 | 0.00 | 17,927 | 3.4 | 0.0008 |
| basic | full4 (v2.1) | 12 | 83% (55-95) | 0 | 0.00 | 16,655 | 3.5 | 0.0007 |
| forms | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 27,339 | 6.5 | 0.0010 |
| forms | full2 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 28,310 | 7.0 | 0.0010 |
| forms | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 33,704 | 8.6 | 0.0012 |
| dialogs | full (v1) | 10 | 100% (72-100) | 0 | 0.30 | 21,191 | 5.3 | 0.0007 |
| dialogs | full2 (v2) | 10 | 100% (72-100) | 0 | 0.30 | 22,412 | 6.0 | 0.0007 |
| dialogs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.20 | 22,470 | 6.2 | 0.0007 |
| frames-tabs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 16,980 | 4.9 | 0.0006 |
| frames-tabs | full2 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 19,336 | 5.6 | 0.0006 |
| frames-tabs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 18,711 | 5.4 | 0.0006 |
| large | full (v1) | 10 | 100% (72-100) | 0 | 0.10 | 117,223 | 5.0 | 0.0047 |
| large | full2 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 33,196 | 4.1 | 0.0015 |
| large | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 30,544 | 4.5 | 0.0014 |
| dynamic | full (v1) | 8 | 100% (68-100) | 0 | 0.00 | 11,577 | 3.0 | 0.0005 |
| dynamic | full2 (v2) | 8 | 100% (68-100) | 0 | 0.00 | 12,657 | 3.2 | 0.0005 |
| dynamic | full4 (v2.1) | 8 | 100% (68-100) | 0 | 0.25 | 12,748 | 3.2 | 0.0005 |

## Kairos on claude-haiku-5-5

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | full (v1) | 60 | 100% (94-100) | 0 | 0.18 | 35,580 | 4.6 | 0.0013 |
| all | full2 (v1 rerun) | 60 | 97% (89-99) | 0 | 0.32 | 39,384 | 4.8 | 0.0014 |
| all | full3 (v2) | 60 | 98% (91-100) | 0 | 0.23 | 26,140 | 4.1 | 0.0010 |
| all | full4 (v2.1) | 60 | 93% (84-97) | 0 | 0.23 | 27,800 | 4.2 | 0.0011 |
| basic | full (v1) | 12 | 100% (76-100) | 0 | 0.00 | 20,498 | 2.5 | 0.0010 |
| basic | full2 (v1 rerun) | 12 | 92% (65-99) | 0 | 0.00 | 20,198 | 2.4 | 0.0009 |
| basic | full3 (v2) | 12 | 100% (76-100) | 0 | 0.00 | 19,780 | 2.3 | 0.0009 |
| basic | full4 (v2.1) | 12 | 83% (55-95) | 0 | 0.00 | 19,433 | 2.5 | 0.0009 |
| forms | full (v1) | 10 | 100% (72-100) | 0 | 0.40 | 33,348 | 5.6 | 0.0012 |
| forms | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.50 | 32,263 | 5.2 | 0.0012 |
| forms | full3 (v2) | 10 | 100% (72-100) | 0 | 0.60 | 34,925 | 5.6 | 0.0013 |
| forms | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.80 | 35,476 | 5.9 | 0.0012 |
| dialogs | full (v1) | 10 | 100% (72-100) | 0 | 0.40 | 27,475 | 5.5 | 0.0009 |
| dialogs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.50 | 27,156 | 5.5 | 0.0009 |
| dialogs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.50 | 27,126 | 5.2 | 0.0009 |
| dialogs | full4 (v2.1) | 10 | 90% (60-98) | 0 | 0.40 | 26,775 | 5.1 | 0.0009 |
| frames-tabs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 17,607 | 3.6 | 0.0008 |
| frames-tabs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.00 | 17,473 | 3.4 | 0.0008 |
| frames-tabs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 18,050 | 3.5 | 0.0007 |
| frames-tabs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 18,052 | 3.5 | 0.0007 |
| large | full (v1) | 10 | 100% (72-100) | 0 | 0.10 | 94,248 | 6.7 | 0.0030 |
| large | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.70 | 115,598 | 8.1 | 0.0036 |
| large | full3 (v2) | 10 | 90% (60-98) | 0 | 0.20 | 39,213 | 5.0 | 0.0017 |
| large | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.20 | 44,583 | 4.6 | 0.0017 |
| dynamic | full (v1) | 8 | 100% (68-100) | 0 | 0.25 | 20,258 | 4.1 | 0.0009 |
| dynamic | full2 (v1 rerun) | 8 | 88% (53-98) | 0 | 0.25 | 19,601 | 4.8 | 0.0011 |
| dynamic | full3 (v2) | 8 | 100% (68-100) | 0 | 0.12 | 18,871 | 3.1 | 0.0008 |
| dynamic | full4 (v2.1) | 8 | 88% (53-98) | 0 | 0.00 | 20,056 | 3.5 | 0.0009 |

## Kairos on glm-5.3-flash

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | full (v1) | 60 | 95% (86-98) | 0 | 0.12 | 20,446 | 4.1 | 0.0022 |
| all | full2 (v1 rerun) | 60 | 95% (86-98) | 0 | 0.15 | 23,650 | 3.7 | 0.0020 |
| all | full3 (v2) | 60 | 100% (94-100) | 0 | 0.15 | 22,020 | 3.6 | 0.0015 |
| all | full4 (v2.1) | 60 | 98% (91-100) | 0 | 0.13 | 20,234 | 3.5 | 0.0014 |
| basic | full (v1) | 12 | 92% (65-99) | 0 | 0.00 | 13,602 | 2.1 | 0.0013 |
| basic | full2 (v1 rerun) | 12 | 92% (65-99) | 0 | 0.00 | 12,872 | 2.1 | 0.0011 |
| basic | full3 (v2) | 12 | 100% (76-100) | 0 | 0.00 | 15,441 | 2.5 | 0.0012 |
| basic | full4 (v2.1) | 12 | 92% (65-99) | 0 | 0.00 | 15,917 | 2.6 | 0.0011 |
| forms | full (v1) | 10 | 100% (72-100) | 0 | 0.60 | 20,976 | 4.0 | 0.0016 |
| forms | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.60 | 21,848 | 4.2 | 0.0020 |
| forms | full3 (v2) | 10 | 100% (72-100) | 0 | 0.50 | 22,460 | 4.3 | 0.0016 |
| forms | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.60 | 22,560 | 4.4 | 0.0015 |
| dialogs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 19,798 | 4.2 | 0.0012 |
| dialogs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.10 | 18,903 | 4.0 | 0.0012 |
| dialogs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.20 | 19,485 | 4.1 | 0.0013 |
| dialogs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.10 | 20,277 | 4.2 | 0.0017 |
| frames-tabs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 13,456 | 2.6 | 0.0011 |
| frames-tabs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.00 | 14,301 | 2.8 | 0.0010 |
| frames-tabs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 13,914 | 2.6 | 0.0013 |
| frames-tabs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 13,923 | 2.6 | 0.0011 |
| large | full (v1) | 10 | 80% (49-94) | 0 | 0.10 | 44,377 | 9.2 | 0.0068 |
| large | full2 (v1 rerun) | 10 | 90% (60-98) | 0 | 0.20 | 63,163 | 6.9 | 0.0055 |
| large | full3 (v2) | 10 | 100% (72-100) | 0 | 0.20 | 46,430 | 5.6 | 0.0026 |
| large | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 33,303 | 4.7 | 0.0021 |
| dynamic | full (v1) | 8 | 100% (68-100) | 0 | 0.00 | 14,808 | 2.6 | 0.0013 |
| dynamic | full2 (v1 rerun) | 8 | 88% (53-98) | 0 | 0.00 | 12,495 | 2.2 | 0.0011 |
| dynamic | full3 (v2) | 8 | 100% (68-100) | 0 | 0.00 | 14,130 | 2.5 | 0.0012 |
| dynamic | full4 (v2.1) | 8 | 100% (68-100) | 0 | 0.12 | 14,764 | 2.4 | 0.0011 |

## Kairos on gpt-6-luna

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | full (v1) | 60 | 92% (82-96) | 0 | 0.22 | 19,213 | 3.5 | 0.0007 |
| all | full2 (v1 rerun) | 60 | 95% (86-98) | 0 | 0.22 | 17,377 | 3.4 | 0.0007 |
| all | full3 (v2) | 60 | 92% (82-96) | 0 | 0.15 | 16,797 | 3.6 | 0.0007 |
| all | full4 (v2.1) | 60 | 93% (84-97) | 0 | 0.15 | 14,444 | 3.3 | 0.0006 |
| basic | full (v1) | 12 | 83% (55-95) | 0 | 0.00 | 12,539 | 2.4 | 0.0007 |
| basic | full2 (v1 rerun) | 12 | 83% (55-95) | 0 | 0.00 | 11,840 | 2.4 | 0.0007 |
| basic | full3 (v2) | 12 | 83% (55-95) | 0 | 0.00 | 13,521 | 2.9 | 0.0008 |
| basic | full4 (v2.1) | 12 | 83% (55-95) | 0 | 0.08 | 15,506 | 3.1 | 0.0007 |
| forms | full (v1) | 10 | 100% (72-100) | 0 | 0.40 | 16,849 | 4.2 | 0.0006 |
| forms | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.40 | 16,766 | 4.1 | 0.0006 |
| forms | full3 (v2) | 10 | 100% (72-100) | 0 | 0.30 | 17,729 | 4.5 | 0.0006 |
| forms | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.30 | 17,436 | 4.4 | 0.0006 |
| dialogs | full (v1) | 10 | 100% (72-100) | 0 | 0.20 | 14,872 | 4.0 | 0.0005 |
| dialogs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.20 | 14,533 | 3.9 | 0.0005 |
| dialogs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.20 | 15,424 | 4.0 | 0.0005 |
| dialogs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.20 | 15,384 | 4.0 | 0.0005 |
| frames-tabs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 10,903 | 2.7 | 0.0004 |
| frames-tabs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.00 | 11,221 | 2.8 | 0.0004 |
| frames-tabs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 10,945 | 2.6 | 0.0004 |
| frames-tabs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 10,959 | 2.6 | 0.0004 |
| large | full (v1) | 10 | 90% (60-98) | 0 | 0.60 | 47,750 | 4.8 | 0.0015 |
| large | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.50 | 37,124 | 4.0 | 0.0013 |
| large | full3 (v2) | 10 | 90% (60-98) | 0 | 0.30 | 32,530 | 5.0 | 0.0011 |
| large | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.20 | 16,111 | 2.9 | 0.0007 |
| dynamic | full (v1) | 8 | 75% (41-93) | 0 | 0.12 | 12,558 | 3.4 | 0.0006 |
| dynamic | full2 (v1 rerun) | 8 | 88% (53-98) | 0 | 0.25 | 10,805 | 3.0 | 0.0006 |
| dynamic | full3 (v2) | 8 | 75% (41-93) | 0 | 0.12 | 9,149 | 2.6 | 0.0006 |
| dynamic | full4 (v2.1) | 8 | 75% (41-93) | 0 | 0.12 | 9,147 | 2.8 | 0.0006 |

## Kairos on gpt-6.1-sol

| scope | run | runs | success | hangs | tool errors/run | tokens/success | calls/task | $/run |
|---|---|---|---|---|---|---|---|---|
| all | full (v1) | 60 | 98% (91-100) | 0 | 0.23 | 18,286 | 3.5 | 0.0122 |
| all | full2 (v1 rerun) | 60 | 97% (89-99) | 0 | 0.30 | 19,153 | 3.4 | 0.0123 |
| all | full3 (v2) | 60 | 97% (89-99) | 0 | 0.15 | 15,229 | 3.3 | 0.0106 |
| all | full4 (v2.1) | 60 | 97% (89-99) | 0 | 0.18 | 15,309 | 3.3 | 0.0106 |
| basic | full (v1) | 12 | 100% (76-100) | 0 | 0.25 | 17,093 | 2.8 | 0.0129 |
| basic | full2 (v1 rerun) | 12 | 100% (76-100) | 0 | 0.25 | 18,558 | 2.8 | 0.0137 |
| basic | full3 (v2) | 12 | 100% (76-100) | 0 | 0.00 | 14,328 | 2.7 | 0.0115 |
| basic | full4 (v2.1) | 12 | 100% (76-100) | 0 | 0.00 | 15,925 | 2.9 | 0.0120 |
| forms | full (v1) | 10 | 100% (72-100) | 0 | 0.50 | 17,414 | 4.2 | 0.0110 |
| forms | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.40 | 16,667 | 4.0 | 0.0108 |
| forms | full3 (v2) | 10 | 100% (72-100) | 0 | 0.40 | 17,220 | 4.0 | 0.0111 |
| forms | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.40 | 17,231 | 4.0 | 0.0111 |
| dialogs | full (v1) | 10 | 90% (60-98) | 0 | 0.20 | 16,792 | 4.4 | 0.0095 |
| dialogs | full2 (v1 rerun) | 10 | 80% (49-94) | 0 | 0.10 | 15,606 | 4.0 | 0.0091 |
| dialogs | full3 (v2) | 10 | 80% (49-94) | 0 | 0.20 | 17,545 | 4.3 | 0.0097 |
| dialogs | full4 (v2.1) | 10 | 80% (49-94) | 0 | 0.40 | 17,075 | 4.3 | 0.0097 |
| frames-tabs | full (v1) | 10 | 100% (72-100) | 0 | 0.00 | 10,911 | 2.7 | 0.0081 |
| frames-tabs | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.00 | 11,231 | 2.8 | 0.0082 |
| frames-tabs | full3 (v2) | 10 | 100% (72-100) | 0 | 0.00 | 11,624 | 2.8 | 0.0084 |
| frames-tabs | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.00 | 11,646 | 2.8 | 0.0084 |
| large | full (v1) | 10 | 100% (72-100) | 0 | 0.20 | 34,274 | 3.9 | 0.0217 |
| large | full2 (v1 rerun) | 10 | 100% (72-100) | 0 | 0.80 | 38,701 | 4.1 | 0.0224 |
| large | full3 (v2) | 10 | 100% (72-100) | 0 | 0.20 | 19,031 | 3.4 | 0.0127 |
| large | full4 (v2.1) | 10 | 100% (72-100) | 0 | 0.20 | 17,399 | 3.2 | 0.0126 |
| dynamic | full (v1) | 8 | 100% (68-100) | 0 | 0.25 | 12,078 | 2.8 | 0.0095 |
| dynamic | full2 (v1 rerun) | 8 | 100% (68-100) | 0 | 0.25 | 12,166 | 2.8 | 0.0086 |
| dynamic | full3 (v2) | 8 | 100% (68-100) | 0 | 0.12 | 11,526 | 2.4 | 0.0097 |
| dynamic | full4 (v2.1) | 8 | 100% (68-100) | 0 | 0.12 | 12,183 | 2.6 | 0.0096 |

## Large-page tasks: mean tokens (in + out) per run and passes (claude-haiku-5-5)

| task | cloak full | cloak full2 | cloak full4 | kairos full | kairos full2 | kairos full3 | kairos full4 | playwright full2 |
|---|---|---|---|---|---|---|---|---|
| large-archive | 385.7k (2/2) | 56.1k (2/2) | 63.2k (2/2) | 179.9k (2/2) | 268.4k (2/2) | 96.7k (1/2) | 108.1k (2/2) | 89.6k (2/2) |
| large-article | 35.8k (2/2) | 17.8k (2/2) | 23.4k (2/2) | 22.8k (2/2) | 45.8k (2/2) | 30.7k (2/2) | 27.3k (2/2) | 18.1k (2/2) |
| large-country | 46.8k (2/2) | 34.1k (2/2) | 34.2k (2/2) | 184.4k (2/2) | 176.2k (2/2) | 54.2k (2/2) | 38.0k (2/2) | 58.6k (2/2) |
| large-order-count | 74.8k (2/2) | 46.7k (2/2) | 20.6k (2/2) | 35.1k (2/2) | 43.2k (2/2) | 27.3k (2/2) | 27.6k (2/2) | 40.7k (2/2) |
| large-order-status | 43.0k (2/2) | 11.3k (2/2) | 11.2k (2/2) | 49.0k (2/2) | 44.4k (2/2) | 22.1k (2/2) | 22.1k (2/2) | 20.5k (2/2) |
| **mean of the 5** | 117.2k | 33.2k | 30.5k | 94.2k | 115.6k | 46.2k | 44.6k | 45.5k |

## The three full3 problems, per phase

| phase | config | wrong-value actions (runs) | literal "a\|b" searches: literal hit / rescued by fallback / no matches | slow or timed-out clicks |
|---|---|---|---|---|
| full | cc-cloak | 0 | 0 / 0 / 0 | 2 |
| full | kairos | 4 | 0 / 0 / 7 | 0 |
| full2 | cc-cloak | 0 | 0 / 0 / 0 | 2 |
| full2 | kairos | 2 | 0 / 0 / 7 | 3 |
| full3 | kairos | 1 | 0 / 0 / 9 | 8 |
| full4 | cc-cloak | 0 | 0 / 0 / 0 | 2 |
| full4 | kairos | 1 | 0 / 6 / 0 | 0 |

Details (full3 and full4):

- full3 kairos wrong-value action: `full3.kairos.claude-haiku-5-5.large-archive.r1` [{'ticket': 'T-0841'}]
- full3 kairos slow click: `full3.kairos.gpt-6-luna.large-archive.r2` call 3 (12.423 s)
- full3 kairos slow click: `full3.kairos.gpt-6.1-sol.large-archive.r1` call 4 (12.41 s)
- full3 kairos slow click: `full3.kairos.claude-haiku-5-5.large-archive.r2` call 3 (12.602 s)
- full3 kairos slow click: `full3.kairos.claude-haiku-5-5.large-archive.r1` call 3 (12.419 s)
- full3 kairos slow click: `full3.kairos.glm-5.3-flash.large-archive.r2` call 3 (12.42 s)
- full3 kairos slow click: `full3.kairos.gpt-6-luna.large-archive.r1` call 4 (12.546 s)
- full3 kairos slow click: `full3.kairos.gpt-6.1-sol.large-archive.r2` call 4 (12.389 s)
- full3 kairos slow click: `full3.kairos.glm-5.3-flash.large-archive.r1` call 3 (12.373 s)
- full3 kairos literal "|" search: `full3.kairos.claude-haiku-5-5.large-article.r1` {"pattern": "rebuilt|Harrow Point|rebuild"} -> no matches
- full3 kairos literal "|" search: `full3.kairos.claude-haiku-5-5.large-article.r2` {"pattern": "rebuil|Harrow Point"} -> no matches
- full3 kairos literal "|" search: `full3.kairos.claude-haiku-5-5.large-order-count.r1` {"pattern": "next|page 2|pagination|load more", "max_results": 5} -> no matches
- full3 kairos literal "|" search: `full3.kairos.gpt-6-luna.large-country.r2` {"pattern": "Shipping country|Save|Uruguay", "regex": false, "case_sensitive": f -> no matches
- full3 kairos literal "|" search: `full3.kairos.gpt-6-luna.large-country.r2` {"pattern": "button|Save|Submit", "regex": false, "case_sensitive": false, "max_ -> no matches
- full3 kairos literal "|" search: `full3.kairos.claude-haiku-5-5.large-country.r2` {"pattern": "save|Save|preferences|button", "max_results": 10} -> no matches
- full3 kairos literal "|" search: `full3.kairos.gpt-6-luna.large-article.r2` {"pattern": "Harrow Point|rebuilt", "regex": false, "case_sensitive": false, "ma -> no matches
- full3 kairos literal "|" search: `full3.kairos.claude-haiku-5-5.large-country.r1` {"pattern": "save|Save|preferences|submit"} -> no matches
- full3 kairos literal "|" search: `full3.kairos.gpt-6-luna.large-country.r1` {"pattern": "Shipping country|Save|button", "regex": false, "case_sensitive": fa -> no matches
- full4 cc-cloak slow click: `full4.cc-cloak.claude-haiku-5-5.tabs-coupon.r1` call 9 (30.284 s)
- full4 cc-cloak slow click: `full4.cc-cloak.claude-haiku-5-5.tabs-coupon.r2` call 9 (30.255 s)
- full4 kairos wrong-value action: `full4.kairos.claude-haiku-5-5.dyn-spa-create.r1` [{'name': 'Orkion'}]
- full4 kairos literal "|" search: `full4.kairos.claude-haiku-5-5.large-article.r1` {"pattern": "rebuil|Harrow Point", "case_sensitive": false} -> rescued by fallback
- full4 kairos literal "|" search: `full4.kairos.glm-5.3-flash.large-country.r1` {"pattern": "save|Save|button"} -> rescued by fallback
- full4 kairos literal "|" search: `full4.kairos.claude-haiku-5-5.large-country.r2` {"pattern": "button|save|Save"} -> rescued by fallback
- full4 kairos literal "|" search: `full4.kairos.gpt-6-luna.large-country.r2` {"pattern": "Shipping country|Save|Save preferences", "regex": false, "case_sens -> rescued by fallback
- full4 kairos literal "|" search: `full4.kairos.gpt-6-luna.large-country.r1` {"pattern": "Shipping country|Save|Uruguay", "regex": false, "case_sensitive": f -> rescued by fallback
- full4 kairos literal "|" search: `full4.kairos.claude-haiku-5-5.large-country.r1` {"pattern": "save|Save|preferences|button", "max_results": 10} -> rescued by fallback

## Search and section-snapshot use (all models)

| phase | config | tool | calls | runs using it | mean result tokens | max |
|---|---|---|---|---|---|---|
| full2 | cc-cloak | search | 33 | 22 | 428 | 3,590 |
| full2 | cc-cloak | snapshot target/depth | 4 | 2 | 110 | 111 |
| full2 | cc-cloak | snapshot whole page | 64 | 31 | 499 | 10,691 |
| full2 | kairos | search | 39 | 33 | 53 | 170 |
| full2 | kairos | snapshot whole page | 45 | 34 | 650 | 4,792 |
| full3 | kairos | search | 52 | 39 | 400 | 5,519 |
| full3 | kairos | snapshot target/depth | 32 | 25 | 820 | 5,207 |
| full3 | kairos | snapshot whole page | 25 | 19 | 141 | 431 |
| full4 | cc-cloak | search | 35 | 21 | 398 | 5,258 |
| full4 | cc-cloak | snapshot whole page | 67 | 33 | 332 | 4,501 |
| full4 | kairos | search | 52 | 43 | 409 | 3,109 |
| full4 | kairos | snapshot target/depth | 23 | 21 | 216 | 1,749 |
| full4 | kairos | snapshot whole page | 33 | 22 | 210 | 2,883 |

## Every full4 failure

- `full4.cc-cloak.claude-haiku-5-5.pub-books-price.r2`: done, answer '£25.27'
- `full4.cc-cloak.claude-haiku-5-5.pub-quotes-author.r2`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.claude-haiku-5-5.dialogs-welcome.r2`: error, no matching 'access' event; got []
- `full4.kairos.claude-haiku-5-5.dyn-spa-create.r1`: done, no matching 'create' event; got [{'name': 'Orkion'}]
- `full4.kairos.claude-haiku-5-5.pub-quotes-author.r1`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.claude-haiku-5-5.pub-quotes-author.r2`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.glm-5.3-flash.pub-quotes-author.r1`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.gpt-6-luna.pub-quotes-author.r1`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.gpt-6-luna.pub-quotes-author.r2`: done, answer 'July 12, 1904 in Parral, Chile'
- `full4.kairos.gpt-6-luna.pub-quotes-scroll.r1`: done, answer 'Albert Einstein'
- `full4.kairos.gpt-6-luna.pub-quotes-scroll.r2`: done, answer 'Ralph Waldo Emerson'
- `full4.kairos.gpt-6.1-sol.pub-js-prompt.r1`: done, answer 'done'
- `full4.kairos.gpt-6.1-sol.pub-js-prompt.r2`: done, answer 'done'
