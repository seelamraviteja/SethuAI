import { useEffect, useState } from "react";
import { api, McpInfo } from "../api";
import { Button, Card } from "./ui";
import badge from "../assets/SethuAI_badge.png";

const STEPS = [
  {
    n: "01",
    title: "Upload a spec",
    body: "Drop in a Swagger / OpenAPI file, paste it, or import from a URL. Every operation becomes one MCP tool automatically.",
  },
  {
    n: "02",
    title: "Review & refine",
    body: "Edit tool names and descriptions, toggle what's exposed, flag destructive calls, set auth — and test each tool against the live API.",
  },
  {
    n: "03",
    title: "Publish & host",
    body: "One click puts every published API live on a single Streamable HTTP endpoint your MCP client connects to.",
  },
];

const FEATURES = [
  ["🔐", "Encrypted secrets", "Credentials are encrypted at rest and write-only from the UI."],
  ["🔑", "Token-gated", "Optional admin & MCP access tokens lock down both surfaces."],
  ["📜", "Full audit log", "Every proxied tool call is recorded and visible in Activity."],
  ["⚡", "Live, no redeploy", "Edits and publishes take effect instantly on /mcp."],
];

export function Landing({ onEnter }: { onEnter: () => void }) {
  const [info, setInfo] = useState<McpInfo | null>(null);

  useEffect(() => {
    api.mcpInfo().then(setInfo).catch(() => {});
  }, []);

  return (
    <div className="fade-up flex flex-col items-center pt-16 text-center sm:pt-24">
      {/* Hero */}
      <div className="relative">
        <div className="absolute inset-0 -z-10 blur-3xl">
          <div className="mx-auto h-32 w-32 rounded-full bg-gradient-to-br from-violet-500/40 to-cyan-400/40" />
        </div>
        <img
          src={badge}
          alt="SethuAI"
          className="h-24 w-24 rounded-full ring-1 ring-white/10 shadow-2xl shadow-violet-900/40"
        />
      </div>

      <h1 className="mt-8 text-5xl font-semibold tracking-tight sm:text-6xl">
        <span className="bg-gradient-to-r from-violet-300 via-white to-cyan-300 bg-clip-text text-transparent">
          SethuAI
        </span>
      </h1>
      <p className="mt-3 text-base text-slate-300">Bridging AI and every system</p>
      <p className="mt-5 max-w-xl text-sm leading-relaxed text-slate-400">
        Turn any Swagger / OpenAPI spec into a hosted{" "}
        <span className="text-slate-200">Model Context Protocol</span> server — with a
        human-in-the-loop review step in between. Generate the tools, refine them, publish,
        and your APIs are instantly callable by any MCP client.
      </p>

      <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
        <Button variant="primary" onClick={onEnter} className="px-6 py-2.5 text-base">
          Open the console →
        </Button>
        {info && (
          <span className="text-xs text-slate-500">
            <span className="text-emerald-300">●</span> {info.published_catalogs} API
            {info.published_catalogs === 1 ? "" : "s"} published · {info.tool_count} tools live
          </span>
        )}
      </div>

      {/* How it works */}
      <div className="mt-20 grid w-full gap-4 text-left sm:grid-cols-3">
        {STEPS.map((s) => (
          <Card key={s.n} className="p-6">
            <div className="bg-gradient-to-r from-violet-300 to-cyan-300 bg-clip-text font-mono text-sm font-semibold text-transparent">
              {s.n}
            </div>
            <div className="mt-3 text-base font-medium text-white">{s.title}</div>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">{s.body}</p>
          </Card>
        ))}
      </div>

      {/* Features */}
      <div className="mt-4 grid w-full gap-3 text-left sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(([icon, title, body]) => (
          <Card key={title} className="p-5">
            <div className="text-xl">{icon}</div>
            <div className="mt-2 text-sm font-medium text-white">{title}</div>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">{body}</p>
          </Card>
        ))}
      </div>

      {/* Endpoint footer */}
      <div className="mt-16 flex items-center gap-3 text-xs text-slate-500">
        <span className="uppercase tracking-wider">Hosted endpoint</span>
        <code className="rounded-md border border-white/10 bg-black/40 px-2.5 py-1 font-mono text-cyan-200">
          {location.origin}/mcp
        </code>
      </div>
    </div>
  );
}
