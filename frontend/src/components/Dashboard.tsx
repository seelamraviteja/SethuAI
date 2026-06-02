import { useEffect, useState } from "react";
import { api, AuditEntry, Catalog, McpInfo } from "../api";
import { Button, Card, MethodBadge, useToast } from "./ui";

export function Dashboard({
  onNew,
  onOpen,
}: {
  onNew: () => void;
  onOpen: (c: Catalog) => void;
}) {
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [info, setInfo] = useState<McpInfo | null>(null);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const [cs, i, a] = await Promise.all([api.list(), api.mcpInfo(), api.audit(40)]);
      setCatalogs(cs);
      setInfo(i);
      setAudit(a.entries);
    } catch (e: any) {
      toast(e.message, "err");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const mcpUrl = `${location.origin}/mcp`;

  return (
    <div className="fade-up space-y-8 pt-10">
      <section className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Bridge your APIs to MCP
          </h1>
          <p className="mt-2 max-w-xl text-sm text-slate-400">
            Upload a Swagger / OpenAPI spec, refine the generated tools, publish — and
            every published API is live on one hosted Streamable HTTP endpoint.
          </p>
        </div>
        <Button variant="primary" onClick={onNew}>
          <span className="text-lg leading-none">+</span> New adapter
        </Button>
      </section>

      <EndpointCard info={info} mcpUrl={mcpUrl} onCopy={() => toast("Endpoint copied")} />

      <section className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
          Adapters
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-slate-400">
            {catalogs.length}
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-500">Loading…</div>
        ) : catalogs.length === 0 ? (
          <Card className="py-16 text-center">
            <div className="text-sm text-slate-400">No adapters yet.</div>
            <button
              onClick={onNew}
              className="mt-3 text-sm font-medium text-cyan-300 hover:text-cyan-200"
            >
              Upload your first spec →
            </button>
          </Card>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {catalogs.map((c) => (
              <CatalogCard
                key={c.id}
                c={c}
                onOpen={() => onOpen(c)}
                onChanged={load}
              />
            ))}
          </div>
        )}
      </section>

      <ActivityPanel entries={audit} onRefresh={load} />
    </div>
  );
}

function SecBadge({ label, on }: { label: string; on: boolean }) {
  return (
    <span
      className={`rounded border px-1.5 py-0.5 text-[10px] tracking-normal ${
        on
          ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
          : "border-amber-400/20 bg-amber-400/10 text-amber-300"
      }`}
    >
      {label} {on ? "🔒" : "open"}
    </span>
  );
}

function ActivityPanel({
  entries,
  onRefresh,
}: {
  entries: AuditEntry[];
  onRefresh: () => void;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
          Activity
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-slate-400">
            audit log
          </span>
        </div>
        <button onClick={onRefresh} className="text-xs text-slate-400 hover:text-slate-200">
          ↻ Refresh
        </button>
      </div>
      <Card className="divide-y divide-white/[0.05] overflow-hidden">
        {entries.length === 0 ? (
          <div className="p-6 text-center text-sm text-slate-500">
            No tool calls yet. Calls via <span className="font-mono">/mcp</span> and the
            Test button appear here.
          </div>
        ) : (
          entries.map((e, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2.5 text-sm">
              <span
                className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                  e.ok ? "bg-emerald-400" : "bg-rose-400"
                }`}
              />
              <MethodBadge method={e.method} />
              <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-300">
                {e.catalog} · {e.tool}
              </span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] ${
                  e.source === "mcp"
                    ? "bg-violet-400/10 text-violet-300"
                    : "bg-white/5 text-slate-400"
                }`}
              >
                {e.source}
              </span>
              <span className="w-12 text-right font-mono text-xs text-slate-400">
                {e.status ?? "—"}
              </span>
              <span className="hidden w-36 text-right text-[11px] text-slate-500 sm:block">
                {new Date(e.ts).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </Card>
    </section>
  );
}

function EndpointCard({
  info,
  mcpUrl,
  onCopy,
}: {
  info: McpInfo | null;
  mcpUrl: string;
  onCopy: () => void;
}) {
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-400">
            <span
              className={`pulse-dot inline-block h-2 w-2 rounded-full ${
                info && info.tool_count > 0 ? "bg-emerald-400" : "bg-slate-500"
              }`}
            />
            Hosted MCP endpoint · Streamable HTTP
            <SecBadge label="API" on={!!info?.admin_protected} />
            <SecBadge label="MCP" on={!!info?.mcp_protected} />
          </div>
          <div className="flex items-center gap-2">
            <code className="rounded-lg border border-white/10 bg-black/40 px-3 py-1.5 font-mono text-sm text-cyan-200">
              {mcpUrl}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(mcpUrl);
                onCopy();
              }}
              className="rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs text-slate-300 hover:bg-white/[0.08]"
            >
              Copy
            </button>
          </div>
        </div>
        <div className="flex gap-6">
          <Stat label="Published APIs" value={info?.published_catalogs ?? 0} />
          <Stat label="Live tools" value={info?.tool_count ?? 0} />
        </div>
      </div>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center">
      <div className="bg-gradient-to-r from-violet-300 to-cyan-300 bg-clip-text text-2xl font-semibold text-transparent">
        {value}
      </div>
      <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
    </div>
  );
}

function CatalogCard({
  c,
  onOpen,
  onChanged,
}: {
  c: Catalog;
  onOpen: () => void;
  onChanged: () => void;
}) {
  const toast = useToast();
  const enabledCount = c.tools.filter((t) => t.enabled).length;

  const toggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      c.published ? await api.unpublish(c.id) : await api.publish(c.id);
      toast(c.published ? "Unpublished" : "Published — now live on /mcp");
      onChanged();
    } catch (err: any) {
      toast(err.message, "err");
    }
  };

  const remove = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete "${c.name}"?`)) return;
    await api.remove(c.id);
    toast("Deleted");
    onChanged();
  };

  return (
    <Card
      className="group cursor-pointer p-5 transition-all duration-150 hover:border-white/20 hover:bg-white/[0.04]"
    >
      <div onClick={onOpen}>
        <div className="flex items-start justify-between">
          <div className="font-medium text-white">{c.name}</div>
          {c.published ? (
            <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300">
              ● Live
            </span>
          ) : (
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-slate-400">
              Draft
            </span>
          )}
        </div>
        <div className="mt-1 truncate font-mono text-xs text-slate-500">{c.base_url || "no base url"}</div>
        <div className="mt-3 text-xs text-slate-400">
          {enabledCount} / {c.tools.length} tools enabled · prefix{" "}
          <span className="font-mono text-slate-300">{c.slug}__</span>
        </div>
      </div>
      <div className="mt-4 flex gap-2 border-t border-white/[0.06] pt-3">
        <Button variant={c.published ? "subtle" : "primary"} onClick={toggle} className="px-3 py-1.5 text-xs">
          {c.published ? "Unpublish" : "Publish"}
        </Button>
        <Button variant="ghost" onClick={onOpen} className="px-3 py-1.5 text-xs">
          Edit
        </Button>
        <Button variant="danger" onClick={remove} className="ml-auto px-3 py-1.5 text-xs">
          Delete
        </Button>
      </div>
    </Card>
  );
}
