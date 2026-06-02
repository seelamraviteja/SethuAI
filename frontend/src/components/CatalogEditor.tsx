import { useState } from "react";
import { api, AuthConfig, Catalog, ToolDef } from "../api";
import { Button, Card, Input, MethodBadge, Toggle, useToast } from "./ui";

export function CatalogEditor({
  initial,
  onBack,
}: {
  initial: Catalog;
  onBack: () => void;
}) {
  const [cat, setCat] = useState<Catalog>(initial);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const patch = (p: Partial<Catalog>) => setCat((c) => ({ ...c, ...p }));
  const patchTool = (id: string, p: Partial<ToolDef>) =>
    setCat((c) => ({
      ...c,
      tools: c.tools.map((t) => (t.id === id ? { ...t, ...p } : t)),
    }));
  const setAllEnabled = (enabled: boolean) =>
    setCat((c) => ({ ...c, tools: c.tools.map((t) => ({ ...t, enabled })) }));

  const save = async (publishAfter = false) => {
    setBusy(true);
    try {
      let saved = await api.update(cat.id, cat);
      if (publishAfter) saved = await api.publish(saved.id);
      setCat(saved);
      toast(publishAfter ? "Saved & published — live on /mcp" : "Saved");
    } catch (e: any) {
      toast(e.message, "err");
    } finally {
      setBusy(false);
    }
  };

  const enabledCount = cat.tools.filter((t) => t.enabled).length;

  return (
    <div className="fade-up space-y-6 pt-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <button onClick={onBack} className="text-sm text-slate-400 hover:text-white">
            ← All adapters
          </button>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-white">
            {cat.name}
          </h1>
          <div className="mt-1 text-xs text-slate-400">
            {enabledCount} / {cat.tools.length} tools · prefix{" "}
            <span className="font-mono text-slate-300">{cat.slug}__</span>
            {cat.published && (
              <span className="ml-2 text-emerald-300">● live</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="subtle" disabled={busy} onClick={() => save(false)}>
            Save
          </Button>
          <Button variant="primary" disabled={busy} onClick={() => save(true)}>
            {cat.published ? "Save & re-publish" : "Publish"}
          </Button>
        </div>
      </div>

      {/* API settings */}
      <Card className="space-y-4 p-5">
        <div className="text-sm font-medium text-slate-200">API settings</div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Display name">
            <Input value={cat.name} onChange={(v) => patch({ name: v })} />
          </Field>
          <Field label="Base URL">
            <Input mono value={cat.base_url} onChange={(v) => patch({ base_url: v })} />
          </Field>
        </div>
        <AuthEditor auth={cat.auth} onChange={(auth) => patch({ auth })} />
      </Card>

      {/* Tools */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-300">Tools</div>
          <div className="flex gap-1.5">
            <button
              onClick={() => setAllEnabled(true)}
              className="rounded-md border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-300 hover:bg-white/[0.08]"
            >
              Enable all
            </button>
            <button
              onClick={() => setAllEnabled(false)}
              className="rounded-md border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-300 hover:bg-white/[0.08]"
            >
              Disable all
            </button>
          </div>
        </div>
        {cat.tools.map((t) => (
          <ToolRow
            key={t.id}
            tool={t}
            catalogId={cat.id}
            onPatch={(p) => patchTool(t.id, p)}
          />
        ))}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-medium text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function AuthEditor({
  auth,
  onChange,
}: {
  auth: AuthConfig;
  onChange: (a: AuthConfig) => void;
}) {
  const set = (p: Partial<AuthConfig>) => onChange({ ...auth, ...p });
  const types: AuthConfig["type"][] = ["none", "apiKey", "bearer", "basic"];

  return (
    <div className="space-y-3 rounded-xl border border-white/[0.06] bg-black/20 p-4">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-slate-400">Auth (service account)</span>
        <div className="flex gap-1">
          {types.map((t) => (
            <button
              key={t}
              onClick={() => set({ type: t })}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                auth.type === t
                  ? "bg-gradient-to-r from-violet-500 to-cyan-400 text-white"
                  : "bg-white/5 text-slate-400 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {auth.type === "apiKey" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Header / query name">
            <Input value={auth.api_key_name} onChange={(v) => set({ api_key_name: v })} placeholder="X-API-Key" />
          </Field>
          <Field label="Location">
            <div className="flex gap-1">
              {(["header", "query"] as const).map((loc) => (
                <button
                  key={loc}
                  onClick={() => set({ api_key_in: loc })}
                  className={`flex-1 rounded-lg px-2 py-2 text-xs ${
                    auth.api_key_in === loc ? "bg-white/10 text-white" : "bg-white/[0.03] text-slate-400"
                  }`}
                >
                  {loc}
                </button>
              ))}
            </div>
          </Field>
          <Field label="Value">
            <Input
              type="password"
              value={auth.api_key_value}
              onChange={(v) => set({ api_key_value: v })}
              placeholder={auth.api_key_set ? "•••• saved — leave blank to keep" : "enter key"}
            />
          </Field>
        </div>
      )}
      {auth.type === "bearer" && (
        <Field label="Bearer token">
          <Input
            type="password"
            mono
            value={auth.bearer_token}
            onChange={(v) => set({ bearer_token: v })}
            placeholder={auth.bearer_set ? "•••• saved — leave blank to keep" : "eyJ…"}
          />
        </Field>
      )}
      {auth.type === "basic" && (
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Username">
            <Input value={auth.username} onChange={(v) => set({ username: v })} />
          </Field>
          <Field label="Password">
            <Input
              type="password"
              value={auth.password}
              onChange={(v) => set({ password: v })}
              placeholder={auth.password_set ? "•••• saved — leave blank to keep" : ""}
            />
          </Field>
        </div>
      )}
      {auth.type === "none" && (
        <p className="text-xs text-slate-500">No credentials sent with proxied requests.</p>
      )}
    </div>
  );
}

function ToolRow({
  tool,
  catalogId,
  onPatch,
}: {
  tool: ToolDef;
  catalogId: string;
  onPatch: (p: Partial<ToolDef>) => void;
}) {
  const [open, setOpen] = useState(false);
  const [args, setArgs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const toast = useToast();

  const runTest = async () => {
    setTesting(true);
    setResult(null);
    try {
      const parsed: Record<string, any> = {};
      for (const [k, v] of Object.entries(args)) {
        if (v === "") continue;
        try {
          parsed[k] = JSON.parse(v);
        } catch {
          parsed[k] = v;
        }
      }
      const r = await api.testTool(catalogId, tool.id, parsed);
      setResult(r.result);
    } catch (e: any) {
      setResult(`Error: ${e.message}`);
    } finally {
      setTesting(false);
    }
  };

  const argNames = [...tool.params.map((p) => p.name), ...(tool.request_body_schema ? ["body"] : [])];

  return (
    <Card className={`overflow-hidden transition-opacity ${tool.enabled ? "" : "opacity-50"}`}>
      <div className="flex items-center gap-3 p-4">
        <Toggle checked={tool.enabled} onChange={(v) => onPatch({ enabled: v })} />
        <MethodBadge method={tool.method} />
        <button onClick={() => setOpen(!open)} className="min-w-0 flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="truncate font-mono text-sm text-white">{tool.tool_name}</span>
            {tool.destructive && (
              <span className="rounded border border-rose-400/20 bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-medium text-rose-300">
                destructive
              </span>
            )}
          </div>
          <div className="truncate font-mono text-xs text-slate-500">{tool.path}</div>
        </button>
        <button
          onClick={() => setOpen(!open)}
          className="text-slate-400 transition-transform hover:text-white"
          style={{ transform: open ? "rotate(180deg)" : "" }}
        >
          ▾
        </button>
      </div>

      {open && (
        <div className="space-y-4 border-t border-white/[0.06] bg-black/20 p-4">
          <Field label="Tool name (identifier the model sees)">
            <Input mono value={tool.tool_name} onChange={(v) => onPatch({ tool_name: v })} />
          </Field>
          <Field label="Description (the model relies on this — make it clear)">
            <textarea
              value={tool.description}
              onChange={(e) => onPatch({ description: e.target.value })}
              className="h-20 w-full resize-none rounded-lg border border-white/10 bg-black/30 p-3 text-sm text-slate-100 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
            />
          </Field>
          <label className="flex items-center gap-2.5">
            <Toggle checked={tool.destructive} onChange={(v) => onPatch({ destructive: v })} />
            <span className="text-xs text-slate-400">
              Mark destructive (flagged to the model in the tool description)
            </span>
          </label>
          <Field label="Request timeout (seconds — blank uses the server default)">
            <Input
              value={tool.timeout_seconds == null ? "" : String(tool.timeout_seconds)}
              onChange={(v) => {
                const n = parseFloat(v);
                onPatch({ timeout_seconds: v.trim() === "" || isNaN(n) ? null : n });
              }}
              placeholder="30"
            />
          </Field>

          {/* Test panel */}
          <div className="rounded-xl border border-white/[0.06] bg-black/30 p-3">
            <div className="mb-2 text-xs font-medium text-slate-400">Test against live API</div>
            {argNames.length === 0 ? (
              <div className="text-xs text-slate-500">No arguments.</div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {argNames.map((name) => (
                  <label key={name} className="space-y-1">
                    <span className="font-mono text-[11px] text-slate-400">{name}</span>
                    <Input
                      mono
                      value={args[name] ?? ""}
                      onChange={(v) => setArgs((a) => ({ ...a, [name]: v }))}
                      placeholder={name === "body" ? '{"json": true}' : "value"}
                    />
                  </label>
                ))}
              </div>
            )}
            <div className="mt-3 flex items-center gap-2">
              <Button variant="subtle" disabled={testing} onClick={runTest} className="px-3 py-1.5 text-xs">
                {testing ? "Calling…" : "▶ Run test"}
              </Button>
            </div>
            {result !== null && (
              <pre
                className={`mt-3 max-h-60 overflow-auto whitespace-pre-wrap rounded-lg border bg-black/50 p-3 font-mono text-[11px] leading-relaxed text-slate-300 ${
                  /^HTTP\s2/.test(result)
                    ? "border-emerald-400/25"
                    : "border-rose-400/25"
                }`}
              >
                {result}
              </pre>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
