import {
  HarvestResponse,
  HarvestSubmit,
  MonitoringSession,
  MonitorStats,
  ReceivedOTP,
  Target,
  TargetCreate,
  TargetDetail,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const API_V1 = `${API_BASE_URL}/api/v1`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_V1}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export const api = {
  getTargets: (skip = 0, limit = 100) =>
    request<Target[]>(`/targets?skip=${skip}&limit=${limit}`),

  createTarget: (data: TargetCreate) =>
    request<Target>("/targets", { method: "POST", body: JSON.stringify(data) }),

  getTarget: (id: string) => request<TargetDetail>(`/targets/${id}`),

  deleteTarget: (id: string) =>
    request<void>(`/targets/${id}`, { method: "DELETE" }),

  getSessions: (statusFilter?: string) =>
    request<MonitoringSession[]>(
      `/monitoring/sessions${statusFilter ? `?status_filter=${statusFilter}` : ""}`
    ),

  getSessionOtps: (sessionId: string) =>
    request<ReceivedOTP[]>(`/monitoring/sessions/${sessionId}/otps`),

  stopSession: (sessionId: string) =>
    request<{ status: string; session_id: string }>(
      `/monitoring/sessions/${sessionId}/stop`,
      { method: "POST" }
    ),

  restartSession: (sessionId: string) =>
    request<{ status: string; session_id: string }>(
      `/monitoring/sessions/${sessionId}/restart`,
      { method: "POST" }
    ),

  getStats: () => request<MonitorStats>("/monitoring/stats"),

  submitHarvest: (data: HarvestSubmit) =>
    request<HarvestResponse>("/harvest/submit", {
      method: "POST",
      body: JSON.stringify(data),
    }),
    
  getBaseUrl: () => API_BASE_URL,
};

export const LIVE_WS_URL = `${API_BASE_URL.replace(/^http/, "ws")}/ws/live`;
