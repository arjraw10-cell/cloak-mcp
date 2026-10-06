# cloak-mcp

A lean MCP server for [CloakBrowser](https://github.com/CloakHQ/CloakBrowser), a source-patched stealth Chromium.
It gives AI agents (Claude Code, Cursor, any MCP client) a real browser that passes bot detection, moves the mouse
and types like a human, and keeps logins in persistent profiles.

It started as a rewrite of `@devinwangd/cloak-browser-mcp` 0.1.x. That server had 80 tools (~7.4k tokens), and in
it a JS `alert()` could freeze the session, many snapshot refs couldn't be clicked, and every action re-sent the
whole page. This one has 20 tools (~1.75k tokens) and none of those problems.

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

**Browsing:** `browser_navigate` (also takes `back`/`forward`/`reload`), `browser_snapshot`, `browser_click`,
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
- **Dialogs can't hang a call.** Actions race against `dialog` and `filechooser` events and report the modal instead
  of blocking.
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
