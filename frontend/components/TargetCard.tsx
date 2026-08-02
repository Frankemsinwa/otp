"use client";

import { Target, TargetStatus } from "@/lib/types";

const statusClass: Record<TargetStatus, string> = {
  ACTIVE: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  EXPIRED: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300",
  RATE_LIMITED: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  IDLE: "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300",
};

const providerDot: Record<string, string> = {
  GMAIL: "bg-red-500",
  YAHOO: "bg-purple-500",
  OTHER: "bg-zinc-400",
};

export function TargetCard({
  target,
  onDelete,
}: {
  target: Target;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 transition-colors hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span
            className={`h-2.5 w-2.5 rounded-full ${providerDot[target.provider] ?? providerDot.OTHER}`}
          />
          <div>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
              {target.email}
            </p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {target.provider}
            </p>
          </div>
        </div>
        <button
          onClick={() => onDelete(target.id)}
          aria-label={`Delete ${target.email}`}
          className="rounded-md px-2 py-1 text-xs font-medium text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/50"
        >
          Delete
        </button>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass[target.status]}`}
        >
          {target.status}
        </span>
        <span className="text-xs text-zinc-400 dark:text-zinc-500">
          {new Date(target.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}
