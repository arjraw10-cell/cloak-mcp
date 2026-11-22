import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { Locator, Page } from "playwright-core";
import type { Session } from "./session.js";

/*
 * Input goes through page.mouse / page.keyboard rather than Locator actions.
 * With humanize on, CloakBrowser patches Locator actions with its own selector
 * resolver, which does not understand Playwright's `aria-ref=` engine, so
 * snapshot refs would fail. page.mouse.click / page.keyboard.type are the
 * humanized primitives (Bezier paths, typing cadence) and take coordinates.
 */

export type ToolResult = {
  content: Array<{ type: "text"; text: string } | { type: "image"; data: string; mimeType: string }>;
  isError?: boolean;
};

export const text = (t: string, isError = false): ToolResult => ({ content: [{ type: "text", text: t }], ...(isError && { isError }) });

/** Snapshot refs: e12 in the first document, f1e12 inside iframes and after the page navigates. */
const SNAPSHOT_REF = /^(f\d+)?e\d+$/;

export function locate(page: Page, ref: string): Locator {
  return SNAPSHOT_REF.test(ref) ? page.locator(`aria-ref=${ref}`) : page.locator(ref);
}

/** Wait until visible, scroll into view, and return a point slightly off-center (humans don't hit dead center). */
export async function pointOf(loc: Locator, timeout: number): Promise<{ x: number; y: number }> {
  // Fail fast on stale refs instead of waiting out the visibility timeout.
  if (String(loc).includes("aria-ref=") && (await loc.count()) === 0) throw new Error("aria-ref not found");
  await loc.waitFor({ state: "visible", timeout });
  await loc.scrollIntoViewIfNeeded({ timeout });
  await assertReceivesInput(loc);
  const box = await loc.boundingBox({ timeout });
  if (!box) throw new Error("Element has no layout box (hidden or detached).");
  const jitter = (size: number) => (Math.random() - 0.5) * Math.min(size * 0.3, 10);
  return { x: box.x + box.width / 2 + jitter(box.width), y: box.y + box.height / 2 + jitter(box.height) };
}

/** Thrown when the target can't receive input; its message is shown to the agent as is. */
class InputBlocked extends Error {}

/**
 * Raw mouse/keyboard input skips Playwright's actionability checks, so an action on an element behind a
 * modal would "succeed" while doing nothing. Refuse when the element is in an inert/aria-hidden subtree, or
 * when something else is topmost at its center (only checked when that center is on screen). The element
 * itself, its descendants, its ancestors (pointer-events: none targets) and its <label> (custom checkboxes
 * over a hidden input) all count as hits.
 */
export async function assertReceivesInput(loc: Locator): Promise<void> {
  const hitTest = (el: Element) => {
    const parent = (n: Node): Node | null => n.parentNode instanceof ShadowRoot ? n.parentNode.host : n.parentNode;
    const within = (n: Node | null, root: Node) => {
      for (; n; n = parent(n)) if (n === root) return true;
      return false;
    };
    for (let n: Node | null = el; n instanceof Element; n = parent(n)) {
      if (n.hasAttribute("inert") || (n !== el && n.getAttribute("aria-hidden") === "true")) return "is inside an inert or aria-hidden part of the page";
    }
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return null; // no area to hit, e.g. a native <select> behind a custom widget
    const top = (el.getRootNode() as Document | ShadowRoot).elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    const labels = "labels" in el && el.labels ? [...(el.labels as NodeListOf<HTMLLabelElement>)] : [];
    if (!top || within(top, el) || within(el, top) || labels.some((l) => within(top, l))) return null;
    const id = top.id ? `#${top.id}` : "";
    const cls = typeof top.className === "string" && top.className.trim() ? `.${top.className.trim().split(/\s+/).slice(0, 2).join(".")}` : "";
    return `is covered by <${top.tagName.toLowerCase()}${id}${cls}>`;
  };
  // Poll briefly so a closing animation or a fading toast doesn't cause a false refusal.
  let blocked: string | null = null;
  for (const end = Date.now() + 1_200; ; await loc.page().waitForTimeout(150)) {
    blocked = await loc.evaluate(hitTest);
    if (!blocked || Date.now() > end) break;
  }
  if (!blocked) return;
  const target = String(loc).match(/aria-ref=(\w+)/)?.[1] ?? String(loc);
  const dialog = openDialog(await loc.page().ariaSnapshot({ mode: "ai", timeout: 10_000 }).catch(() => ""));
  if (dialog) {
    const close = dialog.close ? ` (Close button: ${dialog.close})` : "";
    throw new InputBlocked(`Target ${target} is covered by an open dialog ${dialog.label} — close it first${close}.`);
  }
  throw new InputBlocked(`Target ${target} ${blocked}, so it can't receive input. Check the snapshot below.`);
}

type Button = "left" | "right" | "middle";
export type Modifier = "Alt" | "Control" | "ControlOrMeta" | "Meta" | "Shift";

export async function clickAt(page: Page, x: number, y: number, opts: { button?: Button; doubleClick?: boolean; modifiers?: Modifier[] } = {}): Promise<void> {
  const button = opts.button ?? "left";
  for (const m of opts.modifiers ?? []) await page.keyboard.down(m);
  try {
    if (button === "left" && !opts.doubleClick) {
      await page.mouse.click(x, y);
    } else {
      await page.mouse.move(x, y);
      await page.mouse.down({ button, clickCount: 1 });
      await page.mouse.up({ button, clickCount: 1 });
      if (opts.doubleClick) {
        await page.mouse.down({ button, clickCount: 2 });
        await page.mouse.up({ button, clickCount: 2 });
      }
    }
  } finally {
    for (const m of [...(opts.modifiers ?? [])].reverse()) await page.keyboard.up(m);
  }
}

/** Long text: more than 5 sentences, or over 500 characters (code and lists have few sentence ends). */
export function isLongText(value: string): boolean {
  return value.length > 500 || (value.match(/[.!?]+(\s|$)/g)?.length ?? 0) > 5;
}

// Each key also costs a fixed round trip, so the delays shrink 8x for typing about 4x faster overall.
const FAST_TYPING_DIVISOR = 8;
const TYPING_TIMINGS = ["typing_delay", "typing_delay_spread", "typing_pause_range", "key_hold", "shift_down_delay", "shift_up_delay", "mistype_delay_notice", "mistype_delay_correct"];

/**
 * Humanized typing, about 4x faster for long text so an essay doesn't take minutes.
 * The patched page.keyboard.type ignores per-call config and reads the page's
 * config object (page._humanCfg), so its timings are scaled for this one call.
 */
async function humanType(page: Page, value: string): Promise<void> {
  const cfg = (page as unknown as { _humanCfg?: Record<string, number | number[]> })._humanCfg;
  if (!cfg || !isLongText(value)) return page.keyboard.type(value);
  const saved = TYPING_TIMINGS.map((k) => [k, cfg[k]] as const);
  for (const [k, v] of saved) cfg[k] = Array.isArray(v) ? v.map((n) => n / FAST_TYPING_DIVISOR) : (v as number) / FAST_TYPING_DIVISOR;
  try {
    await page.keyboard.type(value);
  } finally {
    for (const [k, v] of saved) cfg[k] = v;
  }
}

export async function typeInto(page: Page, loc: Locator, value: string, opts: { append?: boolean; humanize: boolean; timeout: number }): Promise<void> {
  if (!opts.humanize) {
    if (opts.append) await loc.pressSequentially(value, { timeout: opts.timeout });
    else await loc.fill(value, { timeout: opts.timeout });
    return;
  }
  const { x, y } = await pointOf(loc, opts.timeout);
  const el = await loc.elementHandle({ timeout: opts.timeout });
  await page.mouse.click(x, y);
  if (!opts.append) {
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.press("Backspace");
  }
  await humanType(page, value);
  // Let the value land before the diff snapshot, so a type that took effect isn't reported as unchanged.
  await page
    .waitForFunction(
      ([el, v]) => ((el as HTMLElement).isContentEditable ? el.textContent : ((el as HTMLInputElement).value ?? el.textContent))?.includes(v),
      [el, value] as const,
      { timeout: 1_000, polling: 50 },
    )
    .catch(() => undefined);
}

/**
 * The innermost (last) dialog or alertdialog in an AI snapshot, with a close/cancel button inside it.
 * The AI snapshot leaves out hidden and aria-hidden nodes, so any dialog listed is a visible one.
 */
export function openDialog(snap: string): { label: string; ref: string; close?: string } | undefined {
  const lines = snap.split("\n");
  let at = -1;
  lines.forEach((l, i) => /^\s*- (alert)?dialog\b.*\[ref=\w+\]/.test(l) && (at = i));
  if (at < 0) return undefined;
  const indent = (l: string) => l.search(/\S/);
  // The snapshot often leaves the dialog's own name out; its first heading is the next best label.
  let name = lines[at].match(/- (?:alert)?dialog "((?:[^"\\]|\\.)*)"/)?.[1];
  let close: string | undefined;
  for (const l of lines.slice(at + 1)) {
    if (indent(l) <= indent(lines[at])) break;
    name ??= l.match(/- heading "((?:[^"\\]|\\.)*)"/)?.[1];
    const m = l.match(/- button "((?:[^"\\]|\\.)*)".*\[ref=(\w+)\]/);
    if (m && !close && /\b(close|dismiss|cancel)\b|^[×✕x]$/i.test(m[1])) close = m[2];
  }
  return { label: name ? `"${name}"` : "(no name)", ref: lines[at].match(/\[ref=(\w+)\]/)![1], close };
}

/**
 * full: the whole snapshot (explicit browser_snapshot). page: the whole snapshot for a small page, a short
 * card for a large one. diff: only changed lines on the same page, else as page. none: no snapshot.
 */
export type SnapshotMode = "full" | "page" | "diff" | "none";

/** Snapshots longer than this come back as a card: the top of the page, an outline, and how to search. */
const LARGE_PAGE_CHARS = 8_000;
const CARD_HEAD_CHARS = 4_000;
const OUTLINE_LINES = 40;
const OUTLINE_ROLE = /^\s*- (heading|table|grid|treegrid|list|listbox|form|search|navigation|main|region|tablist|dialog|alertdialog)\b/;
const ROW_ROLE = /^\s*- (row|listitem|option|treeitem)\b/;

const indentOf = (line: string) => line.length - line.trimStart().length;
const clip = (line: string, n = 300) => (line.length > n ? `${line.slice(0, n)}…` : line);

let savedSnapshots = 0;
/** Write the full snapshot to a temp file (the last 10 are kept) so clients that can read files can grep it. */
function saveSnapshot(snap: string): string {
  const dir = join(tmpdir(), "cloak-mcp-snapshots", String(process.pid));
  mkdirSync(dir, { recursive: true });
  const n = ++savedSnapshots;
  const file = join(dir, `page-${n}.yml`);
  writeFileSync(file, snap);
  rmSync(join(dir, `page-${n - 10}.yml`), { force: true });
  return file;
}

/** Headings, landmarks, forms, and tables/lists with their row counts. */
function outline(lines: string[]): string[] {
  const out: string[] = [];
  for (let i = 0; i < lines.length && out.length < OUTLINE_LINES; i++) {
    if (!OUTLINE_ROLE.test(lines[i])) continue;
    let rows = 0;
    if (/- (table|grid|treegrid|list|listbox)\b/.test(lines[i])) {
      for (let j = i + 1; j < lines.length && indentOf(lines[j]) > indentOf(lines[i]); j++) if (ROW_ROLE.test(lines[j])) rows++;
    }
    out.push(clip(lines[i], 160) + (rows ? ` (${rows} rows)` : ""));
  }
  return out;
}

function largePageCard(lines: string[], snap: string): string {
  let n = 0;
  for (let size = 0; n < lines.length && size + lines[n].length + 1 <= CARD_HEAD_CHARS; n++) size += lines[n].length + 1;
  const head = n ? lines.slice(0, n).join("\n") : clip(lines[0], CARD_HEAD_CHARS);
  const structure = outline(lines);
  return [
    `Snapshot (large page: ${lines.length} lines, ${snap.length} chars; only the top is shown):`,
    head,
    `… ${lines.length - Math.max(n, 1)} more lines.`,
    ...(structure.length ? ["", "Page outline:", ...structure] : []),
    "",
    "To read the rest, use browser_find (text or regex; returns every match with its ref and context, plus the total count) " +
      `or browser_snapshot with target=<ref> for one section. Full snapshot saved to ${saveSnapshot(snap)}`,
  ].join("\n");
}

/**
 * Playwright's AI snapshot: real ARIA roles/names, [ref=eN] handles, iframes included.
 * In diff mode on the same page, only new/changed lines are returned. Playwright keeps refs
 * stable across snapshots, so this cuts a ~30k-char page to the few lines an action touched.
 */
function snapshotText(session: Session, page: Page, snap: string, mode: SnapshotMode): string {
  const lines = snap.split("\n");
  const keys = new Set(lines.map((l) => l.trim())); // ignore re-indentation from inserted wrappers
  const prev = session.lastSnapshot;
  session.lastSnapshot = { page, url: page.url(), keys };
  const max = session.cfg.maxSnapshotChars;

  if (mode === "diff" && prev && prev.page === page && prev.url === page.url()) {
    const added = lines.filter((l) => !prev.keys.has(l.trim()));
    const removed = [...prev.keys].filter((k) => !keys.has(k)).length;
    if (!added.length && !removed) return "Snapshot: unchanged since the last one.";
    const diff = added.join("\n");
    if (diff.length < max / 2) {
      return `Snapshot changes (new or updated lines; ${removed} lines gone; unchanged parts omitted, browser_snapshot shows the full page):\n${diff}`;
    }
  }
  if (mode !== "full" && snap.length > LARGE_PAGE_CHARS) return largePageCard(lines, snap);
  return `Snapshot:\n${truncate(snap, max)}`;
}

function truncate(snap: string, max: number): string {
  if (snap.length <= max) return snap;
  return `${snap.slice(0, max)}\n… [snapshot truncated: ${snap.length - max} more chars. browser_find searches the whole page; full snapshot saved to ${saveSnapshot(snap)}]`;
}

/**
 * Snapshot of one element (target ref) and/or to a limited depth. It doesn't replace the diff baseline,
 * since it is only part of the page.
 */
export async function sectionSnapshot(session: Session, a: { target?: string; depth?: number }): Promise<ToolResult> {
  const page = await session.page();
  if (session.dialog) return text(`A ${session.dialog.type()} dialog is open ("${session.dialog.message().slice(0, 200)}"). Call browser_handle_dialog first.`, true);
  try {
    const opts = { mode: "ai" as const, depth: a.depth, timeout: 10_000 };
    const snap = a.target ? await locate(page, a.target).ariaSnapshot(opts) : await page.ariaSnapshot(opts);
    const what = [a.target && `element ${a.target}`, a.depth && `depth ${a.depth}`].filter(Boolean).join(", ");
    return text(`Page URL: ${page.url()}\nSnapshot (${what}):\n${truncate(snap, session.cfg.maxSnapshotChars)}`);
  } catch (e) {
    const why = explain(e, a.target).replace(/ Use a ref from the fresh snapshot below\.$/, " Get a current ref from browser_find or browser_snapshot.");
    return text(`Error: ${why}`, true);
  }
}

const FIND_CONTEXT = 3;
const FIND_DEFAULT_RESULTS = 20;

/**
 * Search a fresh AI snapshot of the whole page, line by line. Each match is shown with FIND_CONTEXT lines
 * around it under its ancestor path, so a table cell reads as table > row > cell with refs.
 * Ported from Playwright MCP's browser_find (Apache-2.0, Microsoft); adds a default result limit and
 * clips very long lines around the match.
 */
export async function findInPage(session: Session, a: { text?: string; regex?: string; maxResults?: number }): Promise<ToolResult> {
  if (!a.text === !a.regex) return text('Pass exactly one of "text" or "regex".', true);
  let at: (line: string) => number;
  let query: string;
  if (a.regex) {
    const m = a.regex.match(/^\/(.*)\/([a-z]*)$/s);
    let re: RegExp;
    try {
      re = m ? new RegExp(m[1], m[2].replace("g", "")) : new RegExp(a.regex);
    } catch (e) {
      return text(`Invalid regular expression: ${(e as Error).message}`, true);
    }
    at = (l) => l.search(re);
    query = String(re);
  } else {
    const needle = a.text!.toLowerCase();
    at = (l) => l.toLowerCase().indexOf(needle);
    query = `"${a.text}"`;
  }

  const page = await session.page();
  if (session.dialog) return text(`A ${session.dialog.type()} dialog is open ("${session.dialog.message().slice(0, 200)}"). Call browser_handle_dialog first.`, true);
  const lines = (await page.ariaSnapshot({ mode: "ai", timeout: 10_000 })).split("\n");
  const indents = lines.map(indentOf);
  const ancestors = (index: number): number[] => {
    const out: number[] = [];
    for (let i = index - 1, indent = indents[index]; i >= 0 && indent > 0; i--) {
      if (lines[i].trim() && indents[i] < indent) out.push(i), (indent = indents[i]);
    }
    return out.reverse();
  };

  const matched = lines.flatMap((l, i) => (at(l) >= 0 ? [i] : []));
  if (!matched.length) return text(`Page URL: ${page.url()}\nNo matches for ${query}.`);
  const shown = matched.slice(0, a.maxResults ?? FIND_DEFAULT_RESULTS);

  const windows: Array<{ start: number; end: number }> = [];
  for (const m of shown) {
    const start = Math.max(0, m - FIND_CONTEXT);
    const end = Math.min(lines.length - 1, m + FIND_CONTEXT);
    const last = windows[windows.length - 1];
    if (last && start <= last.end + 1) last.end = Math.max(last.end, end);
    else windows.push({ start, end });
  }
  const onPath = new Set<number>();
  for (const m of shown) [m, ...ancestors(m)].forEach((i) => onPath.add(i));
  const isMatch = new Set(shown);
  const render = (i: number) => {
    const l = lines[i];
    if (l.length <= 300 || !isMatch.has(i)) return clip(l);
    const pos = Math.max(0, at(l) - 120);
    return `${l.slice(0, indents[i])}…${l.slice(pos, pos + 300)}…`;
  };
  const snippets = windows.map(({ start, end }) => {
    const idx = [...ancestors(start), ...Array.from({ length: end - start + 1 }, (_, k) => start + k)];
    const out: string[] = [];
    idx.forEach((index, k) => {
      if (k > 0 && index > idx[k - 1] + 1 && !onPath.has(index) && !onPath.has(idx[k - 1])) out.push(`${" ".repeat(indents[index])}...`);
      out.push(render(index));
    });
    return out.join("\n");
  });

  const word = matched.length === 1 ? "match" : "matches";
  const header = shown.length < matched.length
    ? `Found ${matched.length} ${word} for ${query} (showing the first ${shown.length}; raise maxResults for more):`
    : `Found ${matched.length} ${word} for ${query}:`;
  const body = truncate(snippets.join("\n\n----\n\n"), session.cfg.maxSnapshotChars);
  return text(`Page URL: ${page.url()}\n${header}\n\n${body}`);
}

/**
 * Page state block appended to every action result, so the agent never has to guess what happened.
 * lead (the action's summary) comes first, after the "Dialog open" line when a dialog is open.
 */
export async function pageState(session: Session, opts: { snapshot?: SnapshotMode; lead?: string } = {}): Promise<string> {
  const page = session.currentTab();
  const lines: string[] = opts.lead ? [opts.lead, ""] : [];
  if (!page || page.isClosed()) return [...lines, "No open page."].join("\n");
  const tabs = session.listTabs();
  if (session.newTabs.length) {
    const opened = session.newTabs.filter((p) => !p.isClosed()).map((p) => `[${tabs.indexOf(p)}] ${p.url()}`);
    if (opened.length) lines.push(`New tab opened: ${opened.join(", ")} (use browser_tabs select to switch)`);
    session.newTabs = [];
  }
  if (tabs.length > 1) lines.push(`Tabs: ${tabs.length} open, current is [${tabs.indexOf(page)}]`);
  if (session.dialog) {
    const d = session.dialog;
    lines.push(`Modal: ${d.type()} dialog "${d.message().slice(0, 300)}" is blocking the page. Call browser_handle_dialog before anything else.`);
    // The page cannot be snapshotted while a dialog is open.
    lines.splice(opts.lead ? 2 : 0, 0, `Page URL: ${page.url()}`);
    return lines.join("\n");
  }
  if (session.fileChooser) lines.push("Modal: a file chooser is open. Call browser_file_upload with absolute paths.");
  lines.splice(opts.lead ? 2 : 0, 0, `Page URL: ${page.url()}`, `Page title: ${await page.title().catch(() => "")}`);
  if (opts.snapshot !== "none") {
    try {
      const snap = await page.ariaSnapshot({ mode: "ai", timeout: 10_000 });
      const d = openDialog(snap);
      if (d) lines.unshift(`Dialog open: ${d.label} [ref=${d.ref}]${d.close ? ` (Close: [ref=${d.close}])` : ""}. The page behind it may be inert.`);
      lines.push(snapshotText(session, page, snap, opts.snapshot ?? "page"));
    } catch (e) {
      lines.push(`(snapshot unavailable: ${(e as Error).message.split("\n")[0]})`);
    }
  }
  return lines.join("\n");
}

/**
 * After a navigation reaches DOMContentLoaded, give a single-page app up to 8 s to render: no visible
 * indeterminate progress bar, and an interactive element in <main> (or <body>). Never fails; networkidle
 * is no use here because consoles like Google Cloud's never go idle.
 */
export async function waitForRender(page: Page): Promise<void> {
  await page
    .waitForFunction(
      () => {
        const shown = (e: Element) => e.checkVisibility({ opacityProperty: true, visibilityProperty: true });
        if ([...document.querySelectorAll("[role=progressbar]:not([aria-valuenow]), progress:not([value])")].some(shown)) return false;
        const root = document.querySelector("main, [role=main]") ?? document.body;
        const interactive = 'a[href], button, input:not([type=hidden]), select, textarea, [contenteditable=""], [contenteditable=true], [role=button], [role=link], [role=textbox], [role=checkbox], [role=tab], [role=menuitem]';
        return !!root && [...root.querySelectorAll(interactive)].some(shown);
      },
      undefined,
      { timeout: 8_000, polling: 200 },
    )
    .catch(() => undefined);
}

/** Brief settle after an action: let a triggered navigation commit and reach DOMContentLoaded. */
async function settle(page: Page): Promise<void> {
  await page.waitForTimeout(400);
  await page.waitForLoadState("domcontentloaded", { timeout: 5_000 }).catch(() => undefined);
}

function explain(e: unknown, ref?: string): string {
  if (e instanceof InputBlocked) return e.message;
  const msg = e instanceof Error ? e.message : String(e);
  const first = msg.split("\n")[0];
  if (ref && SNAPSHOT_REF.test(ref) && /aria-ref|not found|failed attached|resolved to/i.test(msg)) {
    return `Ref ${ref} no longer exists — the page changed since the last snapshot. Use a ref from the fresh snapshot below.`;
  }
  if (/Timeout .* exceeded/.test(first)) {
    return `${first}. The element may be hidden, covered, or not yet rendered; check the snapshot below.`;
  }
  return first;
}

/**
 * Run a page action, racing it against dialogs/file choosers so a JS alert can't hang the call,
 * then report the resulting page state. Errors also return a fresh snapshot.
 */
export async function act(session: Session, fn: (page: Page) => Promise<string>, opts: { ref?: string; snapshot?: SnapshotMode } = {}): Promise<ToolResult> {
  const page = await session.page();
  if (session.dialog) {
    return text(`A ${session.dialog.type()} dialog is open ("${session.dialog.message().slice(0, 200)}"). Call browser_handle_dialog first.`, true);
  }
  const modal = session.nextModal();
  const work = fn(page);
  work.catch(() => undefined); // may keep running behind an open dialog
  try {
    const outcome = await Promise.race([work, modal.promise.then(() => undefined)]);
    if (outcome !== undefined) await settle(session.currentTab() ?? page);
    const summary = outcome ?? "Action opened a modal.";
    return text(await pageState(session, { snapshot: opts.snapshot ?? "diff", lead: summary }));
  } catch (e) {
    return text(await pageState(session, { lead: `Error: ${explain(e, opts.ref)}` }), true);
  } finally {
    modal.cancel();
  }
}
