export interface ParamDef {
  name: string;
  location: string;
  required: boolean;
  json_schema: any;
  description: string;
}

export interface AuthConfig {
  type: "none" | "apiKey" | "bearer" | "basic";
  api_key_name: string;
  api_key_in: "header" | "query";
  api_key_value: string;
  bearer_token: string;
  username: string;
  password: string;
  // write-only markers from the backend (secret itself is never returned)
  api_key_set: boolean;
  bearer_set: boolean;
  password_set: boolean;
}

export interface ToolDef {
  id: string;
  tool_name: string;
  description: string;
  enabled: boolean;
  destructive: boolean;
  method: string;
  path: string;
  params: ParamDef[];
  request_body_schema: any | null;
  request_body_required: boolean;
}

export interface Catalog {
  id: string;
  name: string;
  description: string;
  base_url: string;
  slug: string;
  auth: AuthConfig;
  tools: ToolDef[];
  published: boolean;
}

export interface McpTool {
  name: string;
  catalog: string;
  method: string;
  path: string;
  destructive: boolean;
}

export interface McpInfo {
  endpoint: string;
  published_catalogs: number;
  tool_count: number;
  tools: McpTool[];
  admin_protected: boolean;
  mcp_protected: boolean;
}

export interface AuditEntry {
  ts: string;
  source: string;
  catalog: string;
  tool: string;
  method: string;
  path: string;
  status: number | null;
  ok: boolean;
  destructive?: boolean;
  error?: string;
}

const TOKEN_KEY = "sethu_admin_token";
export const getToken = () => localStorage.getItem(TOKEN_KEY) ?? "";
export const setToken = (t: string) =>
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);

async function req<T>(url: string, opts?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...opts,
  });
  if (!res.ok) {
    if (res.status === 401) throw new Error("Unauthorized — set a valid admin token (key icon).");
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  parse: (payload: { content?: string; url?: string }) =>
    req<Catalog>("/api/parse", { method: "POST", body: JSON.stringify(payload) }),
  list: () => req<Catalog[]>("/api/catalogs"),
  get: (id: string) => req<Catalog>(`/api/catalogs/${id}`),
  create: (c: Catalog) =>
    req<Catalog>("/api/catalogs", { method: "POST", body: JSON.stringify(c) }),
  update: (id: string, c: Catalog) =>
    req<Catalog>(`/api/catalogs/${id}`, { method: "PUT", body: JSON.stringify(c) }),
  remove: (id: string) => req<{ deleted: boolean }>(`/api/catalogs/${id}`, { method: "DELETE" }),
  publish: (id: string) => req<Catalog>(`/api/catalogs/${id}/publish`, { method: "POST" }),
  unpublish: (id: string) => req<Catalog>(`/api/catalogs/${id}/unpublish`, { method: "POST" }),
  mcpInfo: () => req<McpInfo>("/api/mcp-info"),
  audit: (limit = 50) => req<{ entries: AuditEntry[] }>(`/api/audit?limit=${limit}`),
  testTool: (catalogId: string, toolId: string, args: Record<string, any>) =>
    req<{ result: string }>(`/api/catalogs/${catalogId}/test/${toolId}`, {
      method: "POST",
      body: JSON.stringify({ arguments: args }),
    }),
};
