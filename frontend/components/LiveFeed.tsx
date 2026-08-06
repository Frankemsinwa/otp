"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { LIVE_WS_URL } from "@/lib/api";
import { OTPBroadcast } from "@/lib/types";

interface FeedEntry {
  id: string;
  payload: OTPBroadcast;
  received_at: number;
}

export function LiveFeed() {
  const [entries, setEntries] = useState<FeedEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [highlightedEntryId, setHighlightedEntryId] = useState<string | null>(null); // New state for highlighting
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    const ws = new WebSocket(LIVE_WS_URL);

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as OTPBroadcast;
        const newEntry = { id: crypto.randomUUID(), payload, received_at: Date.now() };
        setEntries((prev) =>
          [
            newEntry,
            ...prev,
          ].slice(0, 100)
        );
        setHighlightedEntryId(newEntry.id); // Highlight the new entry
      } catch {
        // Ignore non-JSON keepalive messages (e.g. "pong").
      }
    };

    ws.onclose = () => {
      setConnected(false);
      retryRef.current = setTimeout(() => connectRef.current(), 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;

    return () => {
      ws.close();
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  }, []);

  useEffect(() => {
    connectRef.current = connect;
    return connect();
  }, [connect]);

  // Effect to clear highlight after a short duration
  useEffect(() => {
    if (highlightedEntryId) {
      const timer = setTimeout(() => {
        setHighlightedEntryId(null);
      }, 1500); // Highlight for 1.5 seconds
      return () => clearTimeout(timer);
    }
  }, [highlightedEntryId]);

  const handleClearFeed = () => {
    setEntries([]);
  };

  return (
    <div className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          Live OTP Feed
        </h2>
        <div className="flex items-center gap-4"> {/* Group connection status and clear button */}
          <button
            onClick={handleClearFeed}
            className="text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
          >
            Clear Feed
          </button>
          <span className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
            <span
              className={`h-2 w-2 rounded-full ${
                connected ? "bg-emerald-500" : "bg-red-500"
              }`}
            />
            {connected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      {entries.length === 0 ? (
        <p className="px-5 py-12 text-center text-sm text-zinc-500 dark:text-zinc-400">
          Waiting for live updates from {LIVE_WS_URL}…
        </p>
      ) : (
        <ul className="max-h-[480px] divide-y divide-zinc-200 overflow-y-auto dark:divide-zinc-800">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className={`px-5 py-3 transition-colors duration-500 ${
                entry.id === highlightedEntryId ? "bg-blue-100 dark:bg-blue-900" : "" // Highlight class
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
                  {entry.payload.target_email}
                </p>
                <code className="shrink-0 rounded bg-zinc-100 px-3 py-1 text-sm font-bold text-zinc-800 dark:bg-zinc-800 dark:text-zinc-100"> {/* Enhanced OTP display */}
                  {entry.payload.extracted_code}
                </code>
              </div>
              {entry.payload.subject && (
                <p className="mt-0.5 truncate text-xs text-zinc-500 dark:text-zinc-400">
                  {entry.payload.subject}
                </p>
              )}
              <div className="mt-1 flex items-center justify-between">
                <span className="text-xs text-zinc-400 dark:text-zinc-500">
                  {entry.payload.sender ?? "unknown sender"}
                </span>
                <span className="text-xs text-zinc-400 dark:text-zinc-500">
                  {new Date(entry.received_at).toLocaleTimeString()}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
