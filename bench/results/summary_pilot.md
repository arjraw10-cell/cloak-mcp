# Results (pilot phase)

42 finished runs, 0 API-error records (re-queued, not counted), total spend $1.33.

Wall-clock times are confounded: cloak-mcp, devinwangd and Kairos use humanized (deliberately slower) input; Playwright MCP does not.

## Static tool-schema cost

| layer | tools | Anthropic tokens | tiktoken o200k |
|---|---|---|---|
| cc-cloak | 20 | 3379 | 2036 |
| cc-devin | 80 | 13213 | 8387 |
| cc-playwright | 25 | 7083 | 4640 |
| cc-devin-default-caps | 34 | 6956 | 4339 |
| kairos | 20 | 3001 | 1818 |

## Spend by model (all phases, including pilot, dev checks and API-error runs)

| model | $ |
|---|---|
| claude-haiku-5-5 | 0.3306 |
| glm-5.3-flash | 0.1471 |
| gpt-6-luna | 0.0500 |
| gpt-6.1-sol | 0.8026 |

## Core comparison (all claude-haiku-5-5, effort low)

### Per config

| group | runs | success (95% CI) | per-repeat success | timeout rate | tool errors/run | tokens per success | tool calls/task | median wall s | $/run | runs with >100K-token requests |
|---|---|---|---|---|---|---|---|---|---|---|
| cc-cloak | 6 | 100% (61-100) | 100% | 0% | 0.00 | 28,152 | 4.8 | 20 | 0.0013 | 0 |
| cc-devin | 6 | 83% (44-97) | 83% | 17% | 0.17 | 64,934 | 5.3 | 15 | 0.0011 | 0 |
| cc-playwright | 6 | 100% (61-100) | 100% | 0% | 0.17 | 37,550 | 5.3 | 11 | 0.0008 | 0 |
| kairos | 6 | 100% (61-100) | 100% | 0% | 0.00 | 23,597 | 4.2 | 12 | 0.0011 | 0 |

## Per config x category (core)

### Per config and category

| group | runs | success (95% CI) | per-repeat success | timeout rate | tool errors/run | tokens per success | tool calls/task | median wall s | $/run | runs with >100K-token requests |
|---|---|---|---|---|---|---|---|---|---|---|
| cc-cloak / basic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 13,351 | 2.0 | 4 | 0.0004 | 0 |
| cc-cloak / dialogs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 23,242 | 6.0 | 9 | 0.0005 | 0 |
| cc-cloak / dynamic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 9,400 | 2.0 | 30 | 0.0008 | 0 |
| cc-cloak / forms | 1 | 100% (21-100) | 100% | 0% | 0.00 | 23,105 | 6.0 | 22 | 0.0007 | 0 |
| cc-cloak / frames-tabs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 25,896 | 10.0 | 38 | 0.0007 | 0 |
| cc-cloak / large | 1 | 100% (21-100) | 100% | 0% | 0.00 | 73,921 | 3.0 | 18 | 0.0048 | 0 |
| cc-devin / basic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 60,773 | 4.0 | 6 | 0.0009 | 0 |
| cc-devin / dialogs | 1 | 0% (0-79) | 0% | 100% | 0.00 | - | 4.0 | 300 | 0.0004 | 0 |
| cc-devin / dynamic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 28,969 | 2.0 | 18 | 0.0020 | 0 |
| cc-devin / forms | 1 | 100% (21-100) | 100% | 0% | 1.00 | 99,484 | 9.0 | 27 | 0.0015 | 0 |
| cc-devin / frames-tabs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 91,620 | 10.0 | 12 | 0.0013 | 0 |
| cc-devin / large | 1 | 100% (21-100) | 100% | 0% | 0.00 | 43,823 | 3.0 | 5 | 0.0006 | 0 |
| cc-playwright / basic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 25,315 | 4.0 | 4 | 0.0005 | 0 |
| cc-playwright / dialogs | 1 | 100% (21-100) | 100% | 0% | 1.00 | 61,819 | 9.0 | 13 | 0.0010 | 0 |
| cc-playwright / dynamic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 15,777 | 2.0 | 30 | 0.0003 | 0 |
| cc-playwright / forms | 1 | 100% (21-100) | 100% | 0% | 0.00 | 34,665 | 5.0 | 9 | 0.0015 | 0 |
| cc-playwright / frames-tabs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 62,970 | 9.0 | 12 | 0.0011 | 0 |
| cc-playwright / large | 1 | 100% (21-100) | 100% | 0% | 0.00 | 24,755 | 3.0 | 6 | 0.0004 | 0 |
| kairos / basic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 17,960 | 2.0 | 6 | 0.0007 | 0 |
| kairos / dialogs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 30,780 | 7.0 | 12 | 0.0010 | 0 |
| kairos / dynamic | 1 | 100% (21-100) | 100% | 0% | 0.00 | 20,120 | 3.0 | 11 | 0.0013 | 0 |
| kairos / forms | 1 | 100% (21-100) | 100% | 0% | 0.00 | 28,087 | 5.0 | 28 | 0.0011 | 0 |
| kairos / frames-tabs | 1 | 100% (21-100) | 100% | 0% | 0.00 | 24,681 | 6.0 | 13 | 0.0010 | 0 |
| kairos / large | 1 | 100% (21-100) | 100% | 0% | 0.00 | 19,955 | 2.0 | 8 | 0.0017 | 0 |

## Kairos native browser tools across models (not compared head-to-head with Claude Code)

### Per model (Kairos)

| group | runs | success (95% CI) | per-repeat success | timeout rate | tool errors/run | tokens per success | tool calls/task | median wall s | $/run | runs with >100K-token requests |
|---|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | 6 | 100% (61-100) | 100% | 0% | 0.00 | 23,597 | 4.2 | 12 | 0.0011 | 0 |
| glm-5.3-flash | 6 | 100% (61-100) | 100% | 0% | 0.00 | 21,175 | 3.7 | 15 | 0.0014 | 0 |
| gpt-6-luna | 6 | 83% (44-97) | 83% | 17% | 0.00 | 16,547 | 4.0 | 18 | 0.0007 | 0 |
| gpt-6.1-sol | 6 | 83% (44-97) | 83% | 17% | 0.00 | 15,740 | 3.0 | 23 | 0.0106 | 0 |

## Per task (core, passes / runs)

| task | cc-cloak | cc-devin | cc-playwright | kairos |
|---|---|---|---|---|
| basic-shop | 1/1 | 1/1 | 1/1 | 1/1 |
| dialogs-draft | 1/1 | 0/1 | 1/1 | 1/1 |
| forms-contact | 1/1 | 1/1 | 1/1 | 1/1 |
| large-order-status | 1/1 | 1/1 | 1/1 | 1/1 |
| pub-quotes-scroll | 1/1 | 1/1 | 1/1 | 1/1 |
| tabs-coupon | 1/1 | 1/1 | 1/1 | 1/1 |

## Where cloak-mcp / Kairos lose (tasks where another core config passed more often)

## Checker sensitivity

Failed answer tasks that a looser 'contains the accepted answer' check would pass (the official score keeps the pre-written exact check):

- none


## Failure candidates (pick the 5 most informative for the write-up)

### pilot.cc-devin.claude-haiku-5-5.dialogs-draft.r1
status `timeout`, 4 calls, 0 tool errors: no matching 'publish' event; got []
```
{"type":"assistant","message":{"model":"claude-haiku-5-5","id":"msg_011ChH3nLwvBrt6hBk5CuAph","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01CgrrCH1moaXmqSCo4EcZYe","name":"mcp__browser__browser_navigate","input":{"url":"http://127.0.0.1:8765/r/ee93c6d01c/draft.html"
{"type":"assistant","message":{"model":"claude-haiku-5-5","id":"msg_011ChH3nLwvBrt6hBk5CuAph","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01M6Fr8Nh5q2foPp1bgbp7vk","name":"mcp__browser__browser_snapshot","input":{},"caller":{"type":"direct"}}],"container":null,"stop
{"type":"user","message":{"role":"user","content":[{"tool_use_id":"toolu_01CgrrCH1moaXmqSCo4EcZYe","type":"tool_result","content":[{"type":"text","text":"Navigated to http://127.0.0.1:8765/r/ee93c6d01c/draft.html\nTitle: Editor\n\nSnapshot:\n- generic \"Newsletter editor\\nHello subscribers, here is
{"type":"user","message":{"role":"user","content":[{"tool_use_id":"toolu_01M6Fr8Nh5q2foPp1bgbp7vk","type":"tool_result","content":[{"type":"text","text":"URL: http://127.0.0.1:8765/r/ee93c6d01c/draft.html\nTitle: Editor\n\n- generic \"Newsletter editor\\nHello subscribers, here is this month's news.
{"type":"assistant","message":{"model":"claude-haiku-5-5","id":"msg_011ChH3nVYMHiicY8iAh6NSF","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_011e96G2jidoeCPoSrdrkJ4A","name":"mcp__browser__browser_click","input":{"target":"e3","element":"Save draft"},"caller":{"type":"
{"type":"assistant","message":{"model":"claude-haiku-5-5","id":"msg_011ChH3nVYMHiicY8iAh6NSF","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_016hBRWepmjLusgqTofyVBdL","name":"mcp__browser__browser_take_screenshot","input":{},"caller":{"type":"direct"}}],"container":nul
```
