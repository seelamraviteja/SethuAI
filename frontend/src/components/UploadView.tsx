import { useState } from "react";
import { api, Catalog } from "../api";
import { Button, Card, useToast } from "./ui";

const SAMPLE = `{
  "openapi": "3.0.0",
  "info": { "title": "Sample Pet Store", "version": "1.0.0" },
  "servers": [{ "url": "https://petstore3.swagger.io/api/v3" }],
  "paths": {
    "/pet/{petId}": {
      "get": {
        "operationId": "getPetById",
        "summary": "Find pet by ID",
        "parameters": [
          { "name": "petId", "in": "path", "required": true, "schema": { "type": "integer" } }
        ]
      }
    }
  }
}`;

export function UploadView({
  onCancel,
  onParsed,
}: {
  onCancel: () => void;
  onParsed: (c: Catalog) => void;
}) {
  const [content, setContent] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const onFile = async (file: File) => {
    setContent(await file.text());
  };

  const generate = async (payload: { content?: string; url?: string }) => {
    setBusy(true);
    try {
      const draft = await api.parse(payload);
      // Persist immediately so the editor works against a real record.
      const saved = await api.create(draft);
      toast(`Generated ${saved.tools.length} tools`);
      onParsed(saved);
    } catch (e: any) {
      toast(e.message, "err");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fade-up space-y-6 pt-10">
      <div>
        <button onClick={onCancel} className="text-sm text-slate-400 hover:text-white">
          ← Back
        </button>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          New adapter
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          Paste an OpenAPI 3.x or Swagger 2.0 spec (JSON or YAML), or drop a file. Each
          operation becomes one MCP tool you can review next.
        </p>
      </div>

      {/* Import from URL */}
      <Card className="p-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <span className="text-xs font-medium text-slate-400 sm:w-32">Import from URL</span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://api.example.com/openapi.json"
            spellCheck={false}
            className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-sm text-slate-100 placeholder:text-slate-500 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
          />
          <Button
            variant="subtle"
            disabled={!url.trim() || busy}
            onClick={() => generate({ url })}
          >
            {busy ? "Fetching…" : "Fetch & generate"}
          </Button>
        </div>
      </Card>

      <div className="flex items-center gap-3 text-xs text-slate-500">
        <div className="h-px flex-1 bg-white/10" /> or paste / upload
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <Card className="p-5">
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files[0];
            if (f) onFile(f);
          }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between">
            <label className="cursor-pointer text-sm font-medium text-cyan-300 hover:text-cyan-200">
              Choose file…
              <input
                type="file"
                accept=".json,.yaml,.yml"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
              />
            </label>
            <button
              onClick={() => setContent(SAMPLE)}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              Load sample
            </button>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste spec JSON / YAML here, or drag a file onto this box…"
            spellCheck={false}
            className="h-80 w-full resize-none rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs leading-relaxed text-slate-200 placeholder:text-slate-600 focus:border-violet-400/50 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
          />
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!content.trim() || busy}
            onClick={() => generate({ content })}
          >
            {busy ? "Generating…" : "Generate tools →"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
