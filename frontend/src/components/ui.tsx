import { createContext, useContext, useState, useCallback, ReactNode } from "react";

const METHOD_COLORS: Record<string, string> = {
  GET: "text-emerald-300 bg-emerald-400/10 border-emerald-400/20",
  POST: "text-sky-300 bg-sky-400/10 border-sky-400/20",
  PUT: "text-amber-300 bg-amber-400/10 border-amber-400/20",
  PATCH: "text-violet-300 bg-violet-400/10 border-violet-400/20",
  DELETE: "text-rose-300 bg-rose-400/10 border-rose-400/20",
};

export function MethodBadge({ method }: { method: string }) {
  const m = method.toUpperCase();
  const cls = METHOD_COLORS[m] ?? "text-slate-300 bg-slate-400/10 border-slate-400/20";
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide ${cls}`}
    >
      {m}
    </span>
  );
}

type BtnProps = {
  children: ReactNode;
  onClick?: (e: React.MouseEvent) => void;
  variant?: "primary" | "ghost" | "danger" | "subtle";
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit";
};

export function Button({
  children,
  onClick,
  variant = "subtle",
  disabled,
  className = "",
  type = "button",
}: BtnProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none";
  const variants: Record<string, string> = {
    primary:
      "text-white shadow-lg shadow-violet-900/30 bg-gradient-to-r from-violet-500 to-cyan-400 hover:brightness-110 active:scale-[0.98]",
    ghost: "text-slate-300 hover:text-white hover:bg-white/5",
    subtle: "text-slate-200 bg-white/[0.04] border border-white/10 hover:bg-white/[0.08]",
    danger: "text-rose-200 bg-rose-500/10 border border-rose-400/20 hover:bg-rose-500/20",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 appearance-none items-center rounded-full transition-colors duration-200 ${
        checked ? "bg-gradient-to-r from-violet-500 to-cyan-400" : "bg-white/10"
      }`}
    >
      <span
        className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}

export function Input({
  value,
  onChange,
  placeholder,
  className = "",
  mono,
  type = "text",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
  mono?: boolean;
  type?: string;
}) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={`w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 transition-colors focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20 ${
        mono ? "font-mono" : ""
      } ${className}`}
    />
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-white/[0.08] bg-white/[0.025] backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  );
}

// ---- Toasts -------------------------------------------------------------
type Toast = { id: number; msg: string; kind: "ok" | "err" };
const ToastCtx = createContext<(msg: string, kind?: "ok" | "err") => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((msg: string, kind: "ok" | "err" = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, msg, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3800);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`fade-up rounded-xl border px-4 py-3 text-sm shadow-xl backdrop-blur ${
              t.kind === "ok"
                ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-100"
                : "border-rose-400/20 bg-rose-500/10 text-rose-100"
            }`}
          >
            {t.msg}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
