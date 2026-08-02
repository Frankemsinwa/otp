"use client";

import { useCallback, useEffect, useState } from "react";
import { Target } from "@/lib/types";
import { api } from "@/lib/api";
import { TargetCard } from "@/components/TargetCard";
import { TargetForm } from "@/components/TargetForm";

export function TargetList() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setTargets(await api.getTargets());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load targets.");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .getTargets()
      .then((data) => {
        if (!cancelled) setTargets(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load targets."
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleDelete(id: string) {
    if (!confirm("Delete this target and all related data?")) return;
    try {
      await api.deleteTarget(id);
      setTargets((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete target.");
    }
  }

  if (loading) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading targets…</p>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}

        {targets.length === 0 ? (
          <p className="rounded-xl border border-dashed border-zinc-300 bg-white px-5 py-12 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400">
            No targets registered yet. Use the form to add one.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {targets.map((target) => (
              <TargetCard key={target.id} target={target} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>

      <div className="lg:col-span-1">
        <TargetForm onCreated={load} />
      </div>
    </div>
  );
}
