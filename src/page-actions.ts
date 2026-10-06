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
  const box = await loc.boundingBox({ timeout });
  if (!box) throw new Error("Element has no layout box (hidden or detached).");
  const jitter = (size: number) => (Math.random() - 0.5) * Math.min(size * 0.3, 10);
  return { x: box.x + box.width / 2 + jitter(box.width), y: box.y + box.height / 2 + jitter(box.height) };
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

export async function typeInto(page: Page, loc: Locator, value: string, opts: { append?: boolean; humanize: boolean; timeout: number }): Promise<void> {
  if (!opts.humanize) {
    if (opts.append) await loc.pressSequentially(value, { timeout: opts.timeout });
    else await loc.fill(value, { timeout: opts.timeout });
    return;
  }
  const { x, y } = await pointOf(loc, opts.timeout);
  await page.mouse.click(x, y);
  if (!opts.append) {
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.press("Backspace");
  }
  await page.keyboard.type(value);
}

export type SnapshotMode = "full" | "diff" | "none";

/**
 * Playwright's AI snapshot: real ARIA roles/names, [ref=eN] handles, iframes included.
 * In diff mode on the same page, only new/changed lines are returned. Playwright keeps refs
 * stable across snapshots, so this cuts a ~30k-char page to the few lines an action touched.
 */
async function snapshotText(session: Session, page: Page, mode: SnapshotMode): Promise<string> {
  const snap = await page.ariaSnapshot({ mode: "ai", timeout: 10_000 });
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
  const body = snap.length > max
    ? `${snap.slice(0, max)}\n… [snapshot truncated: ${snap.length - max} more chars. Scroll, or use browser_evaluate to read specific content]`
    : snap;
  return `Snapshot:\n${body}`;
}

/** Page state block appended to every action result, so the agent never has to guess what happened. */
export async function pageState(session: Session, opts: { snapshot?: SnapshotMode } = {}): Promise<string> {
  const page = session.currentTab();
  if (!page || page.isClosed()) return "No open page.";
  const lines: string[] = [];
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
    return [`Page URL: ${page.url()}`, ...lines].join("\n");
  }
  if (session.fileChooser) lines.push("Modal: a file chooser is open. Call browser_file_upload with absolute paths.");
  lines.unshift(`Page URL: ${page.url()}`, `Page title: ${await page.title().catch(() => "")}`);
  if (opts.snapshot !== "none") {
    try {
      lines.push(await snapshotText(session, page, opts.snapshot ?? "full"));
    } catch (e) {
      lines.push(`(snapshot unavailable: ${(e as Error).message.split("\n")[0]})`);
    }
  }
  return lines.join("\n");
}

/** Brief settle after an action: let a triggered navigation commit and reach DOMContentLoaded. */
async function settle(page: Page): Promise<void> {
  await page.waitForTimeout(400);
  await page.waitForLoadState("domcontentloaded", { timeout: 5_000 }).catch(() => undefined);
}

function explain(e: unknown, ref?: string): string {
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
    return text(`${summary}\n\n${await pageState(session, { snapshot: opts.snapshot ?? "diff" })}`);
  } catch (e) {
    return text(`Error: ${explain(e, opts.ref)}\n\n${await pageState(session)}`, true);
  } finally {
    modal.cancel();
  }
}
