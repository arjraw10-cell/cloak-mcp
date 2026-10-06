import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { basename, isAbsolute, join } from "node:path";
import type { BrowserContext, Dialog, FileChooser, Page } from "playwright-core";
import type { Config } from "./config.js";

export interface ConsoleEntry { type: string; text: string }
export interface NetworkEntry {
  method: string;
  url: string;
  type: string;
  status?: number;
  failure?: string;
  requestHeaders: Record<string, string>;
  responseHeaders?: Record<string, string>;
}

const BUFFER_LIMIT = 500;

/** One browser per server process. Tool calls are serialized so concurrent callers can't interleave. */
export class Session {
  private context?: BrowserContext;
  private launching?: Promise<BrowserContext>;
  private tabs: Page[] = [];
  private current?: Page;
  private queue: Promise<unknown> = Promise.resolve();
  private modalWaiters = new Set<() => void>();
  private consoleLog = new WeakMap<Page, ConsoleEntry[]>();
  private networkLog = new WeakMap<Page, NetworkEntry[]>();
  /** Pages opened by the site (popups, target=_blank) since the last response. */
  newTabs: Page[] = [];
  dialog?: Dialog;
  fileChooser?: FileChooser;
  /** Trimmed lines of the last snapshot, for diffing the next one. */
  lastSnapshot?: { page: Page; url: string; keys: Set<string> };
  /** Profile directory in use, or undefined for an ephemeral session. */
  profileDir?: string;

  constructor(readonly cfg: Config) {
    if (cfg.profile) this.profileDir = this.resolveProfile(cfg.profile);
  }

  serialize<T>(fn: () => Promise<T>): Promise<T> {
    const run = this.queue.then(fn, fn);
    this.queue = run.catch(() => undefined);
    return run;
  }

  /** Current page, launching the browser (or opening a tab) if needed. */
  async page(): Promise<Page> {
    const ctx = await this.ensureContext();
    if (!this.current || this.current.isClosed()) {
      this.current = this.tabs.find((p) => !p.isClosed()) ?? (await ctx.newPage());
      this.newTabs = this.newTabs.filter((p) => p !== this.current); // opened by us, not the site
    }
    return this.current;
  }

  get launched(): boolean {
    return !!this.context;
  }

  get rawContext(): BrowserContext | undefined {
    return this.context;
  }

  listTabs(): Page[] {
    return this.tabs.filter((p) => !p.isClosed());
  }

  currentTab(): Page | undefined {
    return this.current;
  }

  selectTab(index: number): Page {
    const page = this.listTabs()[index];
    if (!page) throw new Error(`No tab at index ${index}. There are ${this.listTabs().length} tabs.`);
    this.current = page;
    return page;
  }

  async newTab(): Promise<Page> {
    const ctx = await this.ensureContext();
    const page = await ctx.newPage();
    this.newTabs = this.newTabs.filter((p) => p !== page);
    this.current = page;
    return page;
  }

  /** Resolves when a dialog or file chooser opens. */
  nextModal(): { promise: Promise<void>; cancel: () => void } {
    let resolve!: () => void;
    const promise = new Promise<void>((r) => (resolve = r));
    this.modalWaiters.add(resolve);
    return { promise, cancel: () => this.modalWaiters.delete(resolve) };
  }

  consoleFor(page: Page): ConsoleEntry[] {
    return this.consoleLog.get(page) ?? [];
  }

  networkFor(page: Page): NetworkEntry[] {
    return this.networkLog.get(page) ?? [];
  }

  async close(): Promise<void> {
    const ctx = this.context;
    this.reset();
    await ctx?.close().catch(() => undefined);
  }

  /** Switch to a named profile (undefined = ephemeral). Relaunches the browser. */
  async useProfile(nameOrPath: string | undefined): Promise<void> {
    await this.close();
    this.profileDir = nameOrPath ? this.resolveProfile(nameOrPath) : undefined;
    await this.ensureContext();
  }

  listProfiles(): string[] {
    if (!existsSync(this.cfg.profilesRoot)) return [];
    return readdirSync(this.cfg.profilesRoot, { withFileTypes: true })
      .filter((e) => e.isDirectory())
      .map((e) => e.name);
  }

  private resolveProfile(nameOrPath: string): string {
    if (isAbsolute(nameOrPath)) return nameOrPath;
    if (!/^[\w-]+$/.test(nameOrPath)) throw new Error("Profile names may only contain letters, digits, _ and -.");
    return join(this.cfg.profilesRoot, nameOrPath);
  }

  /**
   * Each profile keeps its own fingerprint seed so a logged-in identity always
   * presents the same device. Existing profiles adopt --fingerprint-seed once.
   */
  private profileSeed(dir: string): number {
    const file = join(dir, ".cloak-mcp.json");
    try {
      const seed = JSON.parse(readFileSync(file, "utf8")).seed;
      if (Number.isInteger(seed)) return seed;
    } catch {
      /* first use of this profile */
    }
    const seed = this.cfg.seed ?? 1 + Math.floor(Math.random() * 2 ** 31);
    mkdirSync(dir, { recursive: true });
    writeFileSync(file, JSON.stringify({ seed }, null, 2));
    return seed;
  }

  private ensureContext(): Promise<BrowserContext> {
    if (this.context) return Promise.resolve(this.context);
    // Cleared on failure so the next call retries instead of reusing a rejected promise.
    this.launching ??= this.launch().finally(() => (this.launching = undefined));
    return this.launching;
  }

  private async launch(): Promise<BrowserContext> {
    const cb = await import("cloakbrowser");
    const seed = this.profileDir ? this.profileSeed(this.profileDir) : this.cfg.seed;
    const opts = {
      headless: this.cfg.headless,
      humanize: this.cfg.humanize,
      geoip: this.cfg.geoip,
      proxy: this.cfg.proxy,
      timezone: this.cfg.timezone,
      locale: this.cfg.locale,
      viewport: this.cfg.viewport ?? null,
      args: seed !== undefined ? [`--fingerprint=${seed}`] : [],
    };
    let ctx: BrowserContext;
    try {
      ctx = this.profileDir
        ? await cb.launchPersistentContext({ ...opts, userDataDir: this.profileDir })
        : await cb.launchContext(opts);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      const hint = this.profileDir
        ? ` Profile "${basename(this.profileDir)}" may be open in another CloakBrowser window (another MCP client or agent session). Close it, or use a different profile.`
        : "";
      throw new Error(`Browser failed to launch: ${msg.split("\n")[0]}.${hint}`);
    }
    this.context = ctx;
    // A human closing the window must not wedge the session: drop state so the next call relaunches.
    ctx.on("close", () => {
      if (this.context === ctx) this.reset();
    });
    ctx.on("page", (p) => {
      this.attach(p);
      this.newTabs.push(p);
    });
    for (const p of ctx.pages()) this.attach(p);
    this.current = this.tabs[0];
    return ctx;
  }

  private attach(page: Page): void {
    if (this.tabs.includes(page)) return;
    this.tabs.push(page);
    const consoleBuf: ConsoleEntry[] = [];
    this.consoleLog.set(page, consoleBuf);
    const push = <T>(buf: T[], item: T) => {
      buf.push(item);
      if (buf.length > BUFFER_LIMIT) buf.shift();
    };
    page.on("console", (m) => push(consoleBuf, { type: m.type(), text: m.text().slice(0, 2000) }));
    page.on("pageerror", (e) => push(consoleBuf, { type: "pageerror", text: `${e.name}: ${e.message}` }));
    page.on("dialog", (d) => {
      this.dialog = d;
      this.notifyModal();
    });
    page.on("filechooser", (fc) => {
      this.fileChooser = fc;
      this.notifyModal();
    });
    page.on("close", () => {
      this.tabs = this.tabs.filter((p) => p !== page);
      this.newTabs = this.newTabs.filter((p) => p !== page);
      if (this.current === page) this.current = this.tabs[this.tabs.length - 1];
    });

    if (this.cfg.caps.has("network")) {
      const netBuf: NetworkEntry[] = [];
      this.networkLog.set(page, netBuf);
      const byRequest = new WeakMap<object, NetworkEntry>();
      page.on("request", (r) => {
        const entry: NetworkEntry = { method: r.method(), url: r.url(), type: r.resourceType(), requestHeaders: r.headers() };
        byRequest.set(r, entry);
        push(netBuf, entry);
      });
      page.on("response", (r) => {
        const entry = byRequest.get(r.request());
        if (!entry) return;
        entry.status = r.status();
        entry.responseHeaders = r.headers();
      });
      page.on("requestfailed", (r) => {
        const entry = byRequest.get(r);
        if (entry) entry.failure = r.failure()?.errorText ?? "failed";
      });
    }
  }

  private notifyModal(): void {
    for (const w of this.modalWaiters) w();
    this.modalWaiters.clear();
  }

  private reset(): void {
    this.context = undefined;
    this.tabs = [];
    this.newTabs = [];
    this.current = undefined;
    this.dialog = undefined;
    this.fileChooser = undefined;
  }
}
