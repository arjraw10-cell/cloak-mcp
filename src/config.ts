import { homedir } from "node:os";
import { join } from "node:path";

export const CAPS = ["network", "storage", "coords"] as const;
export type Cap = (typeof CAPS)[number];

export interface Config {
  headless: boolean;
  humanize: boolean;
  seed?: number;
  /** Profile name (under profilesRoot) or absolute path. Undefined = ephemeral. */
  profile?: string;
  profilesRoot: string;
  proxy?: string;
  timezone?: string;
  locale?: string;
  geoip: boolean;
  viewport?: { width: number; height: number };
  caps: Set<Cap>;
  actionTimeoutMs: number;
  maxSnapshotChars: number;
}

const HELP = `cloak-mcp — MCP server for CloakBrowser stealth Chromium

  --headless                 Run without a window (default: headed)
  --no-humanize              Disable human-like mouse/keyboard (default: on)
  --fingerprint-seed <int>   Fingerprint seed for ephemeral sessions (profiles store their own)
  --profile <name|path>      Start in a persistent profile (default: ephemeral)
  --profiles-root <dir>      Where named profiles live (default: ~/.cloak-browser-mcp/profiles)
  --proxy <url>              http(s)/socks5 proxy, inline auth allowed
  --geoip                    Derive timezone/locale from the proxy exit IP
  --timezone <iana>          e.g. America/New_York
  --locale <bcp47>           e.g. en-US
  --viewport <WxH>           Fixed viewport (default: follow the window)
  --caps <list|all>          Extra tools: ${CAPS.join(", ")}
  --action-timeout <ms>      Per-action timeout (default 10000)
  --max-snapshot-chars <n>   Truncate snapshots beyond this (default 30000)
`;

export function parseArgs(argv: string[]): Config {
  const cfg: Config = {
    headless: false,
    humanize: true,
    profilesRoot: process.env.CLOAKBROWSER_PROFILES_DIR ?? join(homedir(), ".cloak-browser-mcp", "profiles"),
    geoip: false,
    caps: new Set(),
    actionTimeoutMs: 10_000,
    maxSnapshotChars: 30_000,
  };
  const value = (i: number): string => {
    const v = argv[i + 1];
    if (v === undefined || v.startsWith("--")) throw new Error(`${argv[i]} requires a value`);
    return v;
  };
  const int = (i: number): number => {
    const n = Number.parseInt(value(i), 10);
    if (!Number.isFinite(n)) throw new Error(`${argv[i]} expects an integer`);
    return n;
  };

  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--headless": cfg.headless = true; break;
      case "--headed": cfg.headless = false; break;
      case "--humanize": cfg.humanize = true; break;
      case "--no-humanize": cfg.humanize = false; break;
      case "--fingerprint-seed": cfg.seed = int(i++); break;
      case "--profile":
      case "--profile-dir": cfg.profile = value(i++); break;
      case "--profiles-root": cfg.profilesRoot = value(i++); break;
      case "--proxy": cfg.proxy = value(i++); break;
      case "--geoip": cfg.geoip = true; break;
      case "--timezone": cfg.timezone = value(i++); break;
      case "--locale": cfg.locale = value(i++); break;
      case "--viewport": {
        const m = value(i++).match(/^(\d+)x(\d+)$/);
        if (!m) throw new Error("--viewport must be WIDTHxHEIGHT");
        cfg.viewport = { width: Number(m[1]), height: Number(m[2]) };
        break;
      }
      case "--caps":
        for (const c of value(i++).split(",").map((s) => s.trim()).filter(Boolean)) {
          if (c === "all") CAPS.forEach((x) => cfg.caps.add(x));
          else if ((CAPS as readonly string[]).includes(c)) cfg.caps.add(c as Cap);
          else throw new Error(`Unknown cap "${c}". Valid: ${CAPS.join(", ")}, all`);
        }
        break;
      case "--action-timeout": cfg.actionTimeoutMs = int(i++); break;
      case "--max-snapshot-chars": cfg.maxSnapshotChars = int(i++); break;
      case "-h":
      case "--help":
        process.stderr.write(HELP);
        process.exit(0);
      default:
        throw new Error(`Unknown argument: ${argv[i]}\n\n${HELP}`);
    }
  }
  return cfg;
}
