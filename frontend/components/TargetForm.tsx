"use client";

import { useState } from "react";
import { Provider } from "@/lib/types";
import { api } from "@/lib/api";

export function TargetForm({ onCreated }: { onCreated: () => void }) {
  const [email, setEmail] = useState("");
  const [provider, setProvider] = useState<Provider>(Provider.GMAIL);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await api.createTarget({ email, provider });
      setEmail("");
      setProvider(Provider.GMAIL);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create target.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
        Add Target
      </h2>
      <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">
        Register a new email target profile.
      </p>

      <div className="mt-4 space-y-3">
        <div>
          <label
            htmlFor="target-email"
            className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
          >
            Email
          </label>
          <input
            id="target-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="victim@example.com"
            className="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-zinc-800"
          />
        </div>

        <div>
          <label
            htmlFor="target-provider"
            className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300"
          >
            Provider
          </label>
          <select
            id="target-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
            className="h-10 w-full rounded-lg border border-zinc-300 bg-white px-3 text-sm text-zinc-900 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-200 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-zinc-800"
          >
            <option value={Provider.GMAIL}>Gmail</option>
            <option value={Provider.YAHOO}>Yahoo</option>
            <option value={Provider.OTHER}>Other</option>
          </select>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="mt-4 flex h-10 w-full items-center justify-center rounded-lg bg-zinc-900 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
      >
        {submitting ? "Adding…" : "Add target"}
      </button>
    </form>
  );
}
