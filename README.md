# cloak-mcp

A lean MCP server for [CloakBrowser](https://github.com/CloakHQ/CloakBrowser), a source-patched stealth Chromium.
It gives AI agents (Claude Code, Cursor, any MCP client) a real browser that passes bot detection, moves the mouse
and types like a human, and keeps logins in persistent profiles.

It started as a rewrite of `@devinwangd/cloak-browser-mcp` 0.1.x. That server had 80 tools (13.2k schema tokens),
and in it a JS `alert()` could freeze the session, many snapshot refs couldn't be clicked, and every action re-sent
the whole page. This one has 21 tools (3.8k schema tokens) and none of those problems.

## Benchmark

30 browser tasks (forms, dialogs, iframes/tabs, large pages, dynamic SPAs, plus 8 on public practice sites), each
checked by code, not an LLM judge. Same model everywhere (`claude-haiku-5-5`, effort low), same CloakBrowser
binary, 60 runs per config, November 2026. This is the second full run (cloak-mcp v2, commit 76211fc), with every
config rerun on the identical suite:

| Browser layer | Success (95% CI) | Hangs | Tool errors / run | Tokens per success | Tool calls / task | Schema tokens |
|---|---|---|---|---|---|---|
| **cloak-mcp** (Claude Code) | 100% (94–100) | 0% | **0.05** | **22.5k** | 4.9 | 3,764 |
| Playwright MCP 0.0.86 (Claude Code) | 100% (94–100) | 2% | 0.32 | 40.6k | 6.2 | 7,083 |
| @devinwangd/cloak-browser-mcp, 80 tools (Claude Code) | 82% (70–89) | 17% | 0.30 | 80.1k | 6.6 | 13,213 |
| Kairos native browser tools (Kairos) | 97% (89–99) | 0% | 0.32 | 39.4k | 4.8 | 3,001 |

- **Dialogs:** devinwangd froze on all 10 dialog runs (`alert`, `confirm`, `prompt`) in both runs, until the
  5-minute kill, and failed nothing else. cloak-mcp's click on the same pop-ups returned in under a second, saying
  which dialog was open.
- **Large pages, v1 → v2:** v1 inlined a full snapshot (up to ~10k tokens) on every page load and used 117k tokens
  per successful large-page task, vs 42k for Playwright MCP. v2 returns a short card for big pages and adds
  `browser_find` (see Design notes). Large-page cost fell to 33k per task, the lowest of the four (Playwright MCP:
  46k). The first page result shrank from 8.9k to 1.3k tokens.
- **Where cloak-mcp still loses:** on one large-page task (`large-order-count`, 47k vs Playwright MCP's 41k). And
  small-page tasks cost 4–14% more tokens than in v1, from the extra tool's schema and from agents calling
  `browser_find` where reading the page would do. The configs that didn't change drifted −10% to +16% between the
  two runs, so that is within noise.
- **v2.1 (current, 1d22924):** fixes from a later Kairos run. A match inside a table row now shows the whole row
  (in v2 it could end on the previous row's button), section snapshots no longer make other refs stale, and the
  outline lists dropdowns. Rerun on the same suite: 97% success, 22.8k tokens per success, 30.5k per large-page
  task.
- **Caveats:** v2 was designed after seeing v1's large-page results, so it targets exactly the weakness this suite
  found. It was developed against a separate test page, not the suite's fixtures, but an independent large-page
  test set would make the claim stronger. Unchanged configs moved by up to 3 points in success between runs, so
  cloak-mcp, Playwright MCP and Kairos are within noise of each other on success. Wall-clock time is not compared:
  every layer except Playwright MCP types and clicks with deliberately human-like timing.

Five full runs (1,620 runs) plus the pilot cost $5.09 in total. Tasks, checkers, harness, raw logs and transcripts are in [`bench/`](bench/);
method and rerun commands in [`bench/BENCHMARK.md`](bench/BENCHMARK.md). Tables: v2 in
[`bench/results/summary_full2.md`](bench/results/summary_full2.md), v1 in
[`bench/results/summary.md`](bench/results/summary.md), v1 vs v2 per category in
[`bench/results/compare_v1_v2.md`](bench/results/compare_v1_v2.md), v2.1 plus Kairos's port in
[`bench/results/compare_full4.md`](bench/results/compare_full4.md), and Kairos's latest fixes in
[`bench/results/compare_full5.md`](bench/results/compare_full5.md).

## Setup on any computer

**Supported:** Windows x64, macOS (Apple Silicon and Intel), Linux x64/arm64.
**You need:** [Node.js 20+](https://nodejs.org) and git.

### 1. Clone and build

```bash
git clone https://github.com/arjraw10-cell/cloak-mcp.git
cd cloak-mcp
npm install
npm run build
```

### 2. Download the browser (~200 MB, once per machine)

```bash
npx cloakbrowser install
```

The binary goes into `~/.cloakbrowser/`. You can skip this step, but then the first browser call does the download
and will probably hit the MCP client's timeout.

### 3. Find the absolute path to `dist/index.js`

```bash
# macOS / Linux
echo "$(pwd)/dist/index.js"
# Windows (PowerShell)
"$((Get-Location).Path)\dist\index.js" -replace '\\','/'
```

Use that path below in place of `/ABS/PATH/cloak-mcp/dist/index.js`.

### 4. Register it with your MCP client

**Claude Code** (available in all projects):

```bash
claude mcp add cloakbrowser -s user -- node /ABS/PATH/cloak-mcp/dist/index.js --fingerprint-seed 424242
```

Then run `/mcp` in Claude Code (or restart it) and check that `cloakbrowser` shows as connected.

**Cursor**: add this to `~/.cursor/mcp.json` (`%USERPROFILE%\.cursor\mcp.json` on Windows):

```json
{
  "mcpServers": {
    "cloakbrowser": {
      "command": "node",
      "args": ["/ABS/PATH/cloak-mcp/dist/index.js", "--fingerprint-seed", "424242"]
    }
  }
}
```

**Any other MCP client**: it's a stdio server with command `node` and args `["/ABS/PATH/cloak-mcp/dist/index.js", ...flags]`.

### 5. Check that it works

Ask the agent: *"Use cloakbrowser to run cloak_stealth_audit with probe sannysoft."* A browser window should open, and
every check should come back as passed.

### Updating

```bash
cd cloak-mcp && git pull && npm install && npm run build
```

Then reconnect the server in your client (`/mcp` in Claude Code).

### Platform notes

- **Linux without a display (servers, WSL without GUI):** add `--headless`. If Chromium fails with missing `.so`
  libraries, install them with `sudo npx playwright-core install-deps chromium`.
- **macOS:** if Gatekeeper blocks the downloaded binary, run `npx cloakbrowser info` from the repo to diagnose.
- **Logins don't carry over between computers.** Profiles live in `~/.cloak-browser-mcp/profiles/` on each machine,
  so log in again on the new one. Don't copy profile folders between machines: the fingerprint would no longer
  match the hardware.
- **Newer browser builds:** `npx cloakbrowser login` gets a free key for the latest binary (limited to 1 concurrent
  session). The default free binary needs no key.

## Flags

| Flag | Default | Meaning |
|---|---|---|
| `--headless` | off (headed) | Run without a visible window |
| `--no-humanize` | humanize on | Turn off human-like mouse paths and typing cadence |
| `--fingerprint-seed <int>` | random | Fingerprint seed for ephemeral sessions (profiles store their own) |
| `--profile <name\|path>` | ephemeral | Start in a persistent profile |
| `--profiles-root <dir>` | `~/.cloak-browser-mcp/profiles` | Where named profiles live |
| `--proxy <url>` | none | `http(s)://` or `socks5://`, inline `user:pass@` allowed |
| `--geoip` | off | Derive timezone/locale from the proxy's exit IP |
| `--timezone`, `--locale` | system | e.g. `America/New_York`, `en-US` |
| `--viewport <WxH>` | follows window | Fixed viewport size |
| `--caps <list\|all>` | none | Extra tools: `network`, `storage`, `coords` |
| `--action-timeout <ms>` | 10000 | Per-action timeout |
| `--max-snapshot-chars <n>` | 30000 | Truncate full snapshots beyond this |

## Tools

**Browsing:** `browser_navigate` (also takes `back`/`forward`/`reload`), `browser_snapshot`, `browser_find`, `browser_click`,
`browser_type`, `browser_fill_form`, `browser_select_option`, `browser_hover`, `browser_drag`, `browser_press_key`,
`browser_scroll`, `browser_wait_for`, `browser_take_screenshot`, `browser_evaluate`, `browser_tabs`,
`browser_handle_dialog`, `browser_file_upload`, `browser_console_messages`, `browser_close`

**Cloak:** `cloak_profile` (`list` / `use <name>` / `ephemeral`, switches at runtime), `cloak_stealth_audit`
(in-page checks, or a public probe: sannysoft, creepjs, browserscan, fingerprintjs)

**Opt-in:** `browser_network_requests` (`network`), `browser_storage_state` (`storage`), `browser_mouse_click_xy` (`coords`)

## Design notes

- **Snapshots** come from Playwright's `page.ariaSnapshot({ mode: "ai" })`, which gives real ARIA roles and names,
  `[ref=eN]` handles, and iframe contents.
- **Every action returns the page state.** When the URL stays the same, it returns only the snapshot lines that
  changed (refs are stable across snapshots). On Wikipedia that's ~400 chars instead of ~30k. Errors include a full
  snapshot.
- **Large pages get a card, not the whole page.** When a page's snapshot is over 8,000 characters, navigate (and
  any action that falls back to a full page) returns its top (~4k characters), an outline of headings, landmarks,
  tables with row counts and dropdowns with option counts, and the path of the full snapshot saved to a temp file.
  `browser_find` searches a fresh snapshot of the whole page by text or regex and returns each match with its ref,
  its ancestors, and as context the whole table row or list item holding it (else 3 lines), plus the total count
  (ported from Playwright MCP's, Apache-2.0). A text search for `a|b` with no literal match searches each part. `browser_snapshot` with `target=<ref>`
  (and optional `depth`) reads one section; with no arguments it still returns the full page.
- **Dialogs can't hang a call.** Actions race against `dialog` and `filechooser` events and report the modal instead
  of blocking.
- **Open page dialogs are called out.** When the snapshot holds a visible `dialog` or `alertdialog`, the result's first
  line says so, e.g. `Dialog open: "Verification status" [ref=e572] (Close: [ref=e588]). The page behind it may be
  inert.`
- **No silent success on covered targets.** Before a click, type, hover, drag, select or check, the target must be
  outside any `inert` / `aria-hidden` subtree and be topmost at its center (its own `<label>` counts, so custom
  checkboxes over a hidden input still work). After ~1.2 s of retries, the action is refused with the blocker named,
  e.g. `Target e353 is covered by an open dialog "Verification status" — close it first (Close button: e588).`, plus
  a full snapshot.
- **Navigation waits for the app to render.** After `domcontentloaded`, navigate (also back/forward/reload and
  `browser_tabs new` with a URL) waits up to 8 s for no visible indeterminate progress bar and an interactive element
  in `main` (or `body`), then snapshots whatever is there. No `networkidle`: consoles like Google Cloud's never idle.
- **Typing waits for the value.** After typing, the result waits up to 1 s for the field to contain the text, so a
  late-committing field isn't reported as unchanged.
- **Sandbox on (Windows).** CloakBrowser and Playwright both pass `--no-sandbox` (needed in Linux containers), which
  turns off Chromium's process sandbox and shows an "unsupported command-line flag" bar in profile windows. On Windows
  the server launches without it (`stealthArgs: false` with the default stealth args minus that flag, and
  `chromiumSandbox: true`). Fingerprint and bot-detection results are unchanged.
- **Long text types about 4x faster.** Text with more than 5 sentences, or over 500 characters, is typed with the
  humanized typing delays divided by 8 for that call (each key also costs a fixed round trip), so an essay takes about
  17 s per 360 characters instead of 73 s. Short text keeps normal human speed.
- **Humanize is always on.** Every click, type, hover and drag uses humanized input; there are no tools to toggle it
  or read config (the server's MCP instructions say so). Only the `--no-humanize` launch flag turns it off.
- **Humanize-compatible.** CloakBrowser's humanize patch replaces Locator actions with a resolver that can't read
  `aria-ref` selectors. So clicks and typing go through the humanized `page.mouse` / `page.keyboard` at the element's
  box, and selects/checkboxes use element handles, which the patch leaves alone.
- **stdout stays clean.** cloakbrowser prints update progress with `console.log`, which is redirected to stderr so
  it can't corrupt JSON-RPC.
- **Calls are serialized.** There's one browser per server process, so parallel callers queue instead of
  interleaving.
- **Launch is lazy and recovers.** The browser starts on the first call, a failed launch can be retried, and the
  server relaunches if a human closes the window.
- **Each profile pins its fingerprint seed** in `<profile>/.cloak-mcp.json`, so a logged-in identity always presents
  the same device.
