"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  KeyRound,
  MessageSquare,
  Mail,
  Smartphone,
  Radio,
  Inbox,
} from "lucide-react";
import { LIVE_WS_URL } from "@/lib/api";
import type { LiveEvent } from "@/lib/types";

// ─── Normalized render model ────────────────────────────────────────────────
type FeedKind = "otp" | "sms";
type Channel = "email" | "sms";

interface FeedItem {
  key: string;
  kind: FeedKind;
  channel: Channel;
  targetId: string | null;
  targetEmail: string | null;
  // OTP-specific
  code?: string;
  confidence?: string | null;
  // SMS / generic
  sender: string | null;
  subject?: string | null;
  body?: string | null;
  // timestamps
  receivedAt: string; // ISO from backend
  arrivedAt: number; // Date.now() when we received it (display + ordering)
}

type Filter = "all" | "otp" | "sms";

// ─── Normalization: backend event -> unified FeedItem ───────────────────────
function normalize(ev: LiveEvent): FeedItem {
  const arrivedAt = Date.now();
  if (ev.type === "otp_captured") {
    return {
      key: crypto.randomUUID(),
      kind: "otp",
      channel: "email",
      targetId: ev.target_id,
      targetEmail: ev.target_email,
      code: ev.extracted_code,
      confidence: ev.confidence,
      sender: ev.sender,
      subject: ev.subject,
      receivedAt: ev.captured_at,
      arrivedAt,
    };
  }
  if (ev.type === "new_otp") {
    return {
      key: crypto.randomUUID(),
      kind: "otp",
      channel: "sms",
      targetId: ev.target_id,
      targetEmail: ev.target_email,
      code: ev.otp.code,
      sender: ev.otp.sender,
      subject: ev.otp.snippet,
      receivedAt: ev.otp.received_at,
      arrivedAt,
    };
  }
  // intercepted_sms
  return {
    key: crypto.randomUUID(),
    kind: "sms",
    channel: "sms",
    targetId: ev.target_id,
    targetEmail: ev.target_email,
    sender: ev.sms.sender,
    body: ev.sms.body,
    receivedAt: ev.sms.received_at,
    arrivedAt,
  };
}

// Dedupe key — guards against WS replay / double-broadcast after reconnect.
function dedupeKey(item: FeedItem): string {
  const payload = item.kind === "otp" ? item.code ?? "" : item.body ?? "";
  return `${item.kind}|${item.channel}|${item.receivedAt}|${payload}`;
}

function timeLabel(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleTimeString();
}

// ─── Component ──────────────────────────────────────────────────────────────
export function LiveFeed() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [connected, setConnected] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");

  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seenRef = useRef<Set<string>>(new Set());
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    const ws = new WebSocket(LIVE_WS_URL);

    ws.onopen = () => {
      setConnected(true);
      // Keepalive — backend echoes "pong" for "ping", preventing proxy idle kills.
      if (pingRef.current) clearInterval(pingRef.current);
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, 20_000);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as LiveEvent;
        if (
          payload.type !== "otp_captured" &&
          payload.type !== "new_otp" &&
          payload.type !== "intercepted_sms"
        ) {
          return; // unknown event — ignore
        }
        const item = normalize(payload);
        const dk = dedupeKey(item);
        if (seenRef.current.has(dk)) return;
        seenRef.current.add(dk);
        // Bound the seen-set so it can't grow forever
        if (seenRef.current.size > 500) seenRef.current.clear();

        setItems((prev) => [item, ...prev].slice(0, 200));
      } catch {
        // Non-JSON keepalive ("pong") — safe to ignore.
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (pingRef.current) clearInterval(pingRef.current);
      retryRef.current = setTimeout(() => connectRef.current(), 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connectRef.current = connect;
    connect();
    return () => {
      if (retryRef.current) clearTimeout(retryRef.current);
      if (pingRef.current) clearInterval(pingRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    return items.filter((i) => i.kind === filter);
  }, [items, filter]);

  const counts = useMemo(
    () => ({
      all: items.length,
      otp: items.filter((i) => i.kind === "otp").length,
      sms: items.filter((i) => i.kind === "sms").length,
    }),
    [items],
  );

  return (
    <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      {/* Header + connection status */}
      <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          Live Feed
        </h2>
        <span className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
          <span
            className={`h-2 w-2 rounded-full ${
              connected ? "bg-emerald-500" : "bg-red-500"
            }`}
          />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 border-b border-zinc-200 px-3 py-2 dark:border-zinc-800">
        {(
          [
            ["all", "All", counts.all],
            ["otp", "OTP", counts.otp],
            ["sms", "SMS log", counts.sms],
          ] as [Filter, string, number][]
        ).map(([value, label, count]) => (
          <button
            key={value}
            type="button"
            onClick={() => setFilter(value)}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              filter === value
                ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-100 dark:text-zinc-900"
                : "text-zinc-500 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
            }`}
          >
            {value === "otp" && <KeyRound className="h-3.5 w-3.5" />}
            {value === "sms" && <MessageSquare className="h-3.5 w-3.5" />}
            {value === "all" && <Radio className="h-3.5 w-3.5" />}
            {label}
            <span
              className={`rounded-full px-1.5 text-[10px] ${
                filter === value
                  ? "bg-white/20"
                  : "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400"
              }`}
            >
              {count}
            </span>
          </button>
        ))}
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <p className="flex flex-col items-center gap-2 px-5 py-12 text-center text-sm text-zinc-500 dark:text-zinc-400">
          <Inbox className="h-6 w-6 opacity-40" />
          {items.length === 0
            ? `Waiting for live updates from ${LIVE_WS_URL}…`
            : "No entries for this filter yet."}
        </p>
      ) : (
        <ul className="max-h-[520px] divide-y divide-zinc-200 overflow-y-auto dark:divide-zinc-800">
          {filtered.map((item) => (
            <li
              key={item.key}
              className="px-5 py-3"
              style={{
                borderLeft:
                  item.channel === "sms"
                    ? item.kind === "otp"
                      ? "3px solid rgb(16 185 129)" // emerald for SMS OTP
                      : "3px solid rgb(168 85 247)" // violet for SMS log
                    : "3px solid rgb(14 165 233)", // sky for email OTP
              }}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2">
                  {item.kind === "otp" ? (
                    <KeyRound className="h-4 w-4 shrink-0 text-emerald-500" />
                  ) : (
                    <MessageSquare className="h-4 w-4 shrink-0 text-violet-500" />
                  )}
                  <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {item.targetEmail ?? "Unattributed"}
                  </p>
                  <ChannelBadge channel={item.channel} />
                </div>
                {item.kind === "otp" && item.code ? (
                  <code className="shrink-0 rounded bg-zinc-100 px-2 py-0.5 text-xs font-semibold text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100">
                    {item.code}
                  </code>
                ) : null}
              </div>

              {item.kind === "sms" && item.body ? (
                <p className="mt-1 line-clamp-3 whitespace-pre-wrap break-words text-xs text-zinc-600 dark:text-zinc-300">
                  {item.body}
                </p>
              ) : null}

              {item.subject ? (
                <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
                  {item.subject}
                </p>
              ) : null}

              <div className="mt-1 flex items-center justify-between">
                <span className="text-xs text-zinc-400 dark:text-zinc-500">
                  {item.sender ?? "unknown sender"}
                </span>
                <div className="flex items-center gap-2">
                  {item.kind === "otp" && item.confidence ? (
                    <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                      {Math.round(Number(item.confidence) * 100)}% conf
                    </span>
                  ) : null}
                  <span className="text-xs text-zinc-400 dark:text-zinc-500">
                    {timeLabel(item.receivedAt)}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ChannelBadge({ channel }: { channel: Channel }) {
  if (channel === "sms") {
    return (
      <span className="flex items-center gap-1 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-medium text-violet-700 dark:bg-violet-900/40 dark:text-violet-300">
        <Smartphone className="h-3 w-3" />
        SMS
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-medium text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">
      <Mail className="h-3 w-3" />
      EMAIL
    </span>
  );
}
