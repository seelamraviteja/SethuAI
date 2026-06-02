import { useState } from "react";
import { Catalog, getToken, setToken } from "./api";
import { Button, ToastProvider, useToast } from "./components/ui";
import badge from "./assets/SethuAI_badge.png";
import { Dashboard } from "./components/Dashboard";
import { UploadView } from "./components/UploadView";
import { CatalogEditor } from "./components/CatalogEditor";
import { Landing } from "./components/Landing";

type View =
  | { name: "landing" }
  | { name: "dashboard" }
  | { name: "upload" }
  | { name: "editor"; catalog: Catalog };

export function App() {
  const [view, setView] = useState<View>({ name: "landing" });

  return (
    <ToastProvider>
      <div className="min-h-screen">
        <Header onHome={() => setView({ name: "landing" })} />
        <main className="mx-auto w-full max-w-6xl px-6 pb-24">
          {view.name === "landing" && (
            <Landing onEnter={() => setView({ name: "dashboard" })} />
          )}
          {view.name === "dashboard" && (
            <Dashboard
              onNew={() => setView({ name: "upload" })}
              onOpen={(c) => setView({ name: "editor", catalog: c })}
            />
          )}
          {view.name === "upload" && (
            <UploadView
              onCancel={() => setView({ name: "dashboard" })}
              onParsed={(c) => setView({ name: "editor", catalog: c })}
            />
          )}
          {view.name === "editor" && (
            <CatalogEditor
              initial={view.catalog}
              onBack={() => setView({ name: "dashboard" })}
            />
          )}
        </main>
      </div>
    </ToastProvider>
  );
}

function Header({ onHome }: { onHome: () => void }) {
  const [showKey, setShowKey] = useState(false);
  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-base/70 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <button onClick={onHome} className="group flex items-center gap-3">
          <img
            src={badge}
            alt="SethuAI"
            className="h-10 w-10 rounded-full ring-1 ring-white/10 shadow-lg shadow-violet-900/30 transition-transform group-hover:scale-105"
          />
          <div className="text-left">
            <div className="text-sm font-semibold tracking-tight text-white">SethuAI</div>
            <div className="text-[11px] text-slate-400">Bridging AI and every system</div>
          </div>
        </button>
        <div className="flex items-center gap-4">
          <a
            href="/mcp"
            className="font-mono text-xs text-slate-400 transition-colors hover:text-cyan-300"
          >
            /mcp ↗
          </a>
          <button
            onClick={() => setShowKey(true)}
            title="Admin token"
            className="rounded-lg border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-sm hover:bg-white/[0.08]"
          >
            🔑
          </button>
        </div>
      </div>
      {showKey && <TokenDialog onClose={() => setShowKey(false)} />}
    </header>
  );
}

function TokenDialog({ onClose }: { onClose: () => void }) {
  const [value, setValue] = useState(getToken());
  const toast = useToast();
  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-6 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="fade-up w-full max-w-md rounded-2xl border border-white/10 bg-panel p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-base font-semibold text-white">Admin token</div>
        <p className="mt-1 text-xs text-slate-400">
          Required only if the server sets <code className="text-slate-300">SETHU_ADMIN_TOKEN</code>.
          Stored in this browser and sent as a Bearer token on management requests.
        </p>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          type="password"
          placeholder="paste admin token…"
          className="mt-4 w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2 font-mono text-sm text-slate-100 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              setToken(value.trim());
              toast("Token saved");
              onClose();
            }}
          >
            Save
          </Button>
        </div>
      </div>
    </div>
  );
}
