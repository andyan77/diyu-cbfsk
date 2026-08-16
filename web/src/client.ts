// 后端调用封装。全部走同源相对路径 + credentials: same-origin，
// 让会话 Cookie 自动带上——前端从不持有租户标识，也从不把它放进请求。

export interface UserOut {
  id: string;
  username: string;
  display_name: string;
}

export interface TenantOut {
  id: string;
  slug: string;
  display_name: string;
  role: string;
}

export interface BrandOut {
  id: string;
  code: string;
  display_name: string;
}

export interface DraftTaskOut {
  id: string;
  brand_id: string;
  title: string;
  status: string;
}

export interface SessionOut {
  user: UserOut | null;
  active_tenant: TenantOut | null;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  if (response.status === 204) {
    return undefined as T;
  }
  const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
  if (!response.ok) {
    throw new Error(payload?.detail ?? `HTTP_${response.status}`);
  }
  return payload as T;
}

export const client = {
  readSession: () => request<SessionOut>("GET", "/api/session"),
  login: (username: string, password: string) =>
    request<SessionOut>("POST", "/api/session", { username, password }),
  logout: () => request<void>("DELETE", "/api/session"),
  listTenants: () => request<TenantOut[]>("GET", "/api/tenants"),
  createTenant: (slug: string, displayName: string) =>
    request<TenantOut>("POST", "/api/tenants", { slug, display_name: displayName }),
  selectTenant: (tenantId: string) =>
    request<SessionOut>("PUT", "/api/session/tenant", { tenant_id: tenantId }),
  listBrands: () => request<BrandOut[]>("GET", "/api/brands"),
  createBrand: (code: string, displayName: string) =>
    request<BrandOut>("POST", "/api/brands", { code, display_name: displayName }),
  listDraftTasks: () => request<DraftTaskOut[]>("GET", "/api/draft-tasks"),
  createDraftTask: (brandId: string, title: string) =>
    request<DraftTaskOut>("POST", "/api/draft-tasks", { brand_id: brandId, title })
};
