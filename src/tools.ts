import { readFile } from "node:fs/promises";
import { z } from "zod";
import type { Cap } from "./config.js";
import { act, clickAt, locate, pageState, pointOf, text, typeInto, type ToolResult } from "./page-actions.js";
import type { Session } from "./session.js";

export interface Tool {
  name: string;
  description: string;
  schema: z.ZodObject;
  cap?: Cap;
  handler: (session: Session, args: any) => Promise<ToolResult>;
}

const ref = z.string().describe("Element ref from the latest snapshot, e.g. e12 (a CSS selector also works)");
const modifiers = z.array(z.enum(["Alt", "Control", "ControlOrMeta", "Meta", "Shift"])).optional();

const PROBES = {
  sannysoft: "https://bot.sannysoft.com/",
  creepjs: "https://abrahamjuliot.github.io/creepjs/",
  browserscan: "https://www.browserscan.net/bot-detection",
  fingerprintjs: "https://fingerprintjs.github.io/fingerprintjs/",
} as const;

export const tools: Tool[] = [
  {
    name: "browser_navigate",
    description: "Open a URL in the current tab (launches the browser if needed), or pass back / forward / reload. Returns the page snapshot.",
    schema: z.object({ url: z.string().describe("Absolute URL, or back | forward | reload") }),
    handler: (s, { url }) =>
      act(s, async (page) => {
        const opts = { waitUntil: "domcontentloaded" as const, timeout: 60_000 };
        if (url === "back") await page.goBack(opts);
        else if (url === "forward") await page.goForward(opts);
        else if (url === "reload") await page.reload(opts);
        else await page.goto(url, opts);
        return `Navigated (${url}).`;
      }, { snapshot: "full" }),
  },
  {
    name: "browser_snapshot",
    description: "Accessibility snapshot of the current page with [ref=eN] handles. Every action already returns one; call this only to refresh.",
    schema: z.object({}),
    handler: async (s) => {
      await s.page();
      return text(await pageState(s));
    },
  },
  {
    name: "browser_click",
    description: "Click an element by ref.",
    schema: z.object({
      ref,
      button: z.enum(["left", "right", "middle"]).optional(),
      doubleClick: z.boolean().optional(),
      modifiers,
    }),
    handler: (s, a) =>
      act(
        s,
        async (page) => {
          const { x, y } = await pointOf(locate(page, a.ref), s.cfg.actionTimeoutMs);
          await clickAt(page, x, y, a);
          return `Clicked ${a.ref}.`;
        },
        { ref: a.ref },
      ),
  },
  {
    name: "browser_type",
    description: "Type into an editable element, replacing its content unless append is true. submit presses Enter afterwards.",
    schema: z.object({ ref, text: z.string(), submit: z.boolean().optional(), append: z.boolean().optional() }),
    handler: (s, a) =>
      act(
        s,
        async (page) => {
          await typeInto(page, locate(page, a.ref), a.text, { append: a.append, humanize: s.cfg.humanize, timeout: s.cfg.actionTimeoutMs });
          if (a.submit) await page.keyboard.press("Enter");
          return `Typed into ${a.ref}${a.submit ? " and pressed Enter" : ""}.`;
        },
        { ref: a.ref },
      ),
  },
  {
    name: "browser_fill_form",
    description: "Fill several fields in one call. checkbox/radio take \"true\" or \"false\"; combobox takes the option label.",
    schema: z.object({
      fields: z.array(z.object({ ref, type: z.enum(["textbox", "checkbox", "radio", "combobox"]), value: z.string() })),
    }),
    handler: (s, { fields }) =>
      act(s, async (page) => {
        const timeout = s.cfg.actionTimeoutMs;
        for (const f of fields as Array<{ ref: string; type: string; value: string }>) {
          const loc = locate(page, f.ref);
          if (f.type === "textbox") {
            await typeInto(page, loc, f.value, { humanize: s.cfg.humanize, timeout });
          } else {
            // Element handles bypass the humanize Locator patch, which can't resolve aria refs.
            const el = await loc.elementHandle({ timeout });
            if (!el) throw new Error(`Ref ${f.ref} not found.`);
            if (f.type === "combobox") await el.selectOption({ label: f.value }, { timeout });
            else await el.setChecked(f.value === "true", { timeout });
          }
        }
        return `Filled ${fields.length} field(s).`;
      }),
  },
  {
    name: "browser_select_option",
    description: "Select option(s) in a <select> by label or value.",
    schema: z.object({ ref, values: z.array(z.string()) }),
    handler: (s, a) =>
      act(
        s,
        async (page) => {
          const el = await locate(page, a.ref).elementHandle({ timeout: s.cfg.actionTimeoutMs });
          if (!el) throw new Error(`Ref ${a.ref} not found.`);
          const picked = await el.selectOption(a.values, { timeout: s.cfg.actionTimeoutMs });
          return `Selected ${picked.join(", ")}.`;
        },
        { ref: a.ref },
      ),
  },
  {
    name: "browser_hover",
    description: "Move the mouse over an element.",
    schema: z.object({ ref }),
    handler: (s, a) =>
      act(
        s,
        async (page) => {
          const { x, y } = await pointOf(locate(page, a.ref), s.cfg.actionTimeoutMs);
          await page.mouse.move(x, y);
          return `Hovered ${a.ref}.`;
        },
        { ref: a.ref },
      ),
  },
  {
    name: "browser_drag",
    description: "Drag one element onto another.",
    schema: z.object({ startRef: ref, endRef: ref }),
    handler: (s, a) =>
      act(s, async (page) => {
        const from = await pointOf(locate(page, a.startRef), s.cfg.actionTimeoutMs);
        const to = await pointOf(locate(page, a.endRef), s.cfg.actionTimeoutMs);
        await page.mouse.move(from.x, from.y);
        await page.mouse.down();
        await page.mouse.move(to.x, to.y, { steps: 12 });
        await page.mouse.up();
        return `Dragged ${a.startRef} to ${a.endRef}.`;
      }),
  },
  {
    name: "browser_press_key",
    description: "Press a key or combo on the focused element, e.g. Enter, Escape, ArrowDown, Control+A.",
    schema: z.object({ key: z.string() }),
    handler: (s, { key }) =>
      act(s, async (page) => {
        await page.keyboard.press(key);
        return `Pressed ${key}.`;
      }),
  },
  {
    name: "browser_scroll",
    description: "Scroll with the mouse wheel, over an element if ref is given (for inner scroll areas).",
    schema: z.object({
      direction: z.enum(["down", "up", "left", "right"]).optional(),
      amount: z.number().optional().describe("Pixels, default 600"),
      ref: ref.optional(),
    }),
    handler: (s, a) =>
      act(s, async (page) => {
        if (a.ref) {
          const { x, y } = await pointOf(locate(page, a.ref), s.cfg.actionTimeoutMs);
          await page.mouse.move(x, y);
        }
        const n = a.amount ?? 600;
        const d = a.direction ?? "down";
        await page.mouse.wheel(d === "left" ? -n : d === "right" ? n : 0, d === "up" ? -n : d === "down" ? n : 0);
        return `Scrolled ${d} ${n}px.`;
      }),
  },
  {
    name: "browser_wait_for",
    description: "Wait for text to appear, text to disappear, or a number of seconds.",
    schema: z.object({ text: z.string().optional(), textGone: z.string().optional(), seconds: z.number().optional() }),
    handler: (s, a) =>
      act(s, async (page) => {
        if (a.seconds) await page.waitForTimeout(Math.min(a.seconds, 60) * 1000);
        if (a.text) await page.getByText(a.text).first().waitFor({ state: "visible", timeout: 30_000 });
        if (a.textGone) await page.getByText(a.textGone).first().waitFor({ state: "hidden", timeout: 30_000 });
        if (!a.seconds && !a.text && !a.textGone) throw new Error("Pass text, textGone, or seconds.");
        return "Wait finished.";
      }),
  },
  {
    name: "browser_take_screenshot",
    description: "Screenshot of the viewport, the full page, or one element. Prefer the snapshot for reading and acting; use this for visual checks.",
    schema: z.object({ ref: ref.optional(), fullPage: z.boolean().optional(), path: z.string().optional().describe("Also save to this absolute path") }),
    handler: async (s, a) => {
      const page = await s.page();
      const opts = { type: "png" as const, ...(a.path && { path: a.path }) };
      const buf = a.ref
        ? await locate(page, a.ref).screenshot({ ...opts, timeout: s.cfg.actionTimeoutMs })
        : await page.screenshot({ ...opts, fullPage: !!a.fullPage });
      return { content: [{ type: "image", data: buf.toString("base64"), mimeType: "image/png" }] };
    },
  },
  {
    name: "browser_evaluate",
    description: "Run a JS function in the page and return its JSON result, e.g. () => document.title. With ref, the function receives the element. Runs in the page's own JS world.",
    schema: z.object({ function: z.string(), ref: ref.optional() }),
    handler: (s, a) =>
      act(
        s,
        async (page) => {
          let result: unknown;
          if (a.ref) {
            const el = await locate(page, a.ref).elementHandle({ timeout: s.cfg.actionTimeoutMs });
            if (!el) throw new Error(`Ref ${a.ref} not found.`);
            result = await el.evaluate(new Function("el", `return (${a.function})(el)`) as (el: unknown) => unknown);
          } else {
            result = await page.evaluate(`(${a.function})()`);
          }
          return `Result:\n${JSON.stringify(result, null, 2) ?? "undefined"}`;
        },
        { ref: a.ref, snapshot: "none" },
      ),
  },
  {
    name: "browser_tabs",
    description: "List, open, select, or close tabs. index is 0-based; close without index closes the current tab.",
    schema: z.object({ action: z.enum(["list", "new", "select", "close"]), index: z.number().optional(), url: z.string().optional() }),
    handler: async (s, a) => {
      await s.page();
      if (a.action === "new") {
        const page = await s.newTab();
        if (a.url) return act(s, async () => (await page.goto(a.url, { waitUntil: "domcontentloaded" }), "Opened new tab."));
      } else if (a.action === "select") {
        s.selectTab(a.index ?? 0);
      } else if (a.action === "close") {
        const page = a.index === undefined ? s.currentTab() : s.listTabs()[a.index];
        if (!page) throw new Error(`No tab at index ${a.index}.`);
        await page.close();
        await s.page();
      }
      const list = s.listTabs().map((p, i) => `${p === s.currentTab() ? "*" : " "} [${i}] ${p.url()}`);
      return text(`${list.join("\n")}\n\n${await pageState(s, { snapshot: a.action === "list" ? "none" : "full" })}`);
    },
  },
  {
    name: "browser_handle_dialog",
    description: "Accept or dismiss the open alert/confirm/prompt dialog.",
    schema: z.object({ accept: z.boolean(), promptText: z.string().optional() }),
    handler: async (s, a) => {
      const d = s.dialog;
      if (!d) return text("No dialog is open.", true);
      s.dialog = undefined;
      await (a.accept ? d.accept(a.promptText) : d.dismiss()).catch(() => undefined);
      const page = await s.page();
      await page.waitForTimeout(300);
      return text(`${a.accept ? "Accepted" : "Dismissed"} ${d.type()} dialog.\n\n${await pageState(s)}`);
    },
  },
  {
    name: "browser_file_upload",
    description: "Provide files to the open file chooser. Click the upload control first to open it.",
    schema: z.object({ paths: z.array(z.string()).describe("Absolute file paths") }),
    handler: async (s, { paths }) => {
      const fc = s.fileChooser;
      if (!fc) return text("No file chooser is open. Click the upload button/input first.", true);
      s.fileChooser = undefined;
      await fc.setFiles(paths);
      return text(`Uploaded ${paths.length} file(s).\n\n${await pageState(s)}`);
    },
  },
  {
    name: "browser_console_messages",
    description: "Console output and uncaught page errors for the current tab.",
    schema: z.object({ errorsOnly: z.boolean().optional() }),
    handler: async (s, a) => {
      const msgs = s.consoleFor(await s.page()).filter((m) => !a.errorsOnly || m.type === "error" || m.type === "pageerror");
      return text(msgs.length ? msgs.slice(-200).map((m) => `[${m.type}] ${m.text}`).join("\n") : "(no console messages)");
    },
  },
  {
    name: "browser_close",
    description: "Close the browser. The next browser tool relaunches it.",
    schema: z.object({}),
    handler: async (s) => {
      await s.close();
      return text("Browser closed.");
    },
  },
  {
    name: "cloak_profile",
    description:
      "Persistent profiles keep logins, cookies and a fixed fingerprint. list shows them; use relaunches the browser in a profile (created if new); ephemeral relaunches with a throwaway one. Only use a profile when the task needs a login.",
    schema: z.object({ action: z.enum(["list", "use", "ephemeral"]), name: z.string().optional() }),
    handler: async (s, a) => {
      if (a.action === "list") {
        const names = s.listProfiles();
        const active = s.profileDir ?? "(ephemeral)";
        return text(`Active: ${active}\nProfiles in ${s.cfg.profilesRoot}:\n${names.map((n) => `  ${n}`).join("\n") || "  (none)"}`);
      }
      if (a.action === "use" && !a.name) return text("Pass name for action=use.", true);
      await s.useProfile(a.action === "use" ? a.name : undefined);
      return text(`Relaunched in ${s.profileDir ?? "an ephemeral profile"}.\n\n${await pageState(s)}`);
    },
  },
  {
    name: "cloak_stealth_audit",
    description: "Check for automation leaks. No probe: in-page checks (webdriver, UA, WebGL, timezone...). probe: load a public bot-detection page and return its verdict text (navigates the current tab).",
    schema: z.object({ probe: z.enum(Object.keys(PROBES) as [keyof typeof PROBES]).optional() }),
    handler: async (s, a) => {
      const page = await s.page();
      if (a.probe) {
        const url = PROBES[a.probe as keyof typeof PROBES];
        await page.goto(url, { waitUntil: "load", timeout: 60_000 });
        await page.waitForTimeout(4_000); // probes compute asynchronously
        return text(`Probe ${url}:\n\n${await page.evaluate("document.body.innerText.slice(0, 6000)")}`);
      }
      const report = await page.evaluate(`(() => {
        const gl = document.createElement("canvas").getContext("webgl");
        const dbg = gl && gl.getExtension("WEBGL_debug_renderer_info");
        return {
          webdriver: navigator.webdriver,
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          languages: navigator.languages,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          hardwareConcurrency: navigator.hardwareConcurrency,
          deviceMemory: navigator.deviceMemory ?? null,
          plugins: navigator.plugins.length,
          webglVendor: dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : null,
          webglRenderer: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null,
          screen: screen.width + "x" + screen.height,
        };
      })()`);
      return text(JSON.stringify(report, null, 2));
    },
  },

  // ---- opt-in via --caps ----
  {
    name: "browser_network_requests",
    cap: "network",
    description: "Requests made by the current tab. Without index: a list (newest last). With index: that request's headers.",
    schema: z.object({ filter: z.string().optional().describe("URL substring"), index: z.number().optional() }),
    handler: async (s, a) => {
      const all = s.networkFor(await s.page());
      if (a.index !== undefined) {
        const r = all[a.index];
        if (!r) return text(`No request at index ${a.index}.`, true);
        const fmt = (h?: Record<string, string>) => Object.entries(h ?? {}).map(([k, v]) => `  ${k}: ${v}`).join("\n");
        return text(`${r.method} ${r.url} → ${r.status ?? r.failure ?? "pending"}\nRequest headers:\n${fmt(r.requestHeaders)}\nResponse headers:\n${fmt(r.responseHeaders)}`);
      }
      const rows = all
        .map((r, i) => ({ r, i }))
        .filter(({ r }) => !a.filter || r.url.includes(a.filter))
        .slice(-150)
        .map(({ r, i }) => `[${i}] ${r.method} ${r.status ?? r.failure ?? "…"} ${r.type} ${r.url}`);
      return text(rows.join("\n") || "(no requests)");
    },
  },
  {
    name: "browser_storage_state",
    cap: "storage",
    description: "save writes cookies + localStorage to a JSON file; load restores the cookies from such a file into the current session.",
    schema: z.object({ action: z.enum(["save", "load"]), path: z.string().describe("Absolute path to the JSON file") }),
    handler: async (s, a) => {
      await s.page();
      const ctx = s.rawContext!;
      if (a.action === "save") {
        const state = await ctx.storageState({ path: a.path });
        return text(`Saved ${state.cookies.length} cookies and ${state.origins.length} origins' storage to ${a.path}.`);
      }
      const state = JSON.parse(await readFile(a.path, "utf8"));
      await ctx.addCookies(state.cookies ?? []);
      return text(`Loaded ${state.cookies?.length ?? 0} cookies. localStorage is not restored; use cloak_profile for full persistence.`);
    },
  },
  {
    name: "browser_mouse_click_xy",
    cap: "coords",
    description: "Click at viewport pixel coordinates, for canvas or elements missing from the snapshot.",
    schema: z.object({ x: z.number(), y: z.number(), button: z.enum(["left", "right", "middle"]).optional(), doubleClick: z.boolean().optional() }),
    handler: (s, a) =>
      act(s, async (page) => {
        await clickAt(page, a.x, a.y, a);
        return `Clicked at (${a.x}, ${a.y}).`;
      }),
  },
];
