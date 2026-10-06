#!/usr/bin/env node
// stdout is the JSON-RPC channel. cloakbrowser logs download/update progress with
// console.log, which would corrupt the protocol mid-session, so route it to stderr.
// Must run before cloakbrowser is (dynamically) imported.
console.log = console.error;
console.info = console.error;

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { parseArgs } from "./config.js";
import { text } from "./page-actions.js";
import { Session } from "./session.js";
import { tools } from "./tools.js";

let cfg;
try {
  cfg = parseArgs(process.argv.slice(2));
} catch (e) {
  process.stderr.write(`cloak-mcp: ${(e as Error).message}\n`);
  process.exit(2);
}

const session = new Session(cfg);
const enabled = tools.filter((t) => !t.cap || cfg.caps.has(t.cap));
const byName = new Map(enabled.map((t) => [t.name, t]));

/** Plain JSON Schema without the per-tool "$schema" URL (~14 tokens x every tool). */
function inputSchema(schema: z.ZodObject) {
  const { $schema: _, ...json } = z.toJSONSchema(schema) as Record<string, unknown>;
  return json as { type: "object"; [k: string]: unknown };
}

const server = new Server({ name: "cloak-mcp", version: "0.1.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: enabled.map((t) => ({ name: t.name, description: t.description, inputSchema: inputSchema(t.schema) })),
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const tool = byName.get(req.params.name);
  if (!tool) return text(`Unknown tool ${req.params.name}.`, true);
  const parsed = tool.schema.safeParse(req.params.arguments ?? {});
  if (!parsed.success) return text(`Invalid arguments: ${z.prettifyError(parsed.error)}`, true);
  try {
    return await session.serialize(() => tool.handler(session, parsed.data));
  } catch (e) {
    return text(`Error: ${(e as Error).message.split("\n")[0]}`, true);
  }
});

const shutdown = async () => {
  await session.close();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.stdin.on("close", shutdown);

await server.connect(new StdioServerTransport());
