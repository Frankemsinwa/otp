import { Target } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const LIVE_WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export const api = {
  getTargets: async (): Promise<Target[]> => {
    const res = await fetch(`${API_BASE}/api/targets`);
    if (!res.ok) throw new Error("Failed to fetch targets");
    return res.json();
  },
  deleteTarget: async (id: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/targets/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete target");
  }
};
