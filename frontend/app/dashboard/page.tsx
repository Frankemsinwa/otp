import type { Metadata } from "next";
import Link from "next/link";
import { api } from "@/lib/api";
import { TargetStatus } from "@/lib/types";

export const metadata: Metadata = {
  title: "Dashboard",
};

async function getStats() {
  try {
    return await api.getStats();
  } catch {
    return { total_targets: 0, active_sessions: 0, otps_captured_24h: 0 };
  }
}

async function getTargets() {
  try {
    return await api.getTargets(0, 5);
  } catch {
    return [];
  }
}

function statusBadgeClass(status: TargetStatus) {
  switch (status) {
    case TargetStatus.ACTIVE:
      return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300";
    case TargetStatus.EXPIRED:
      return "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300";
    case TargetStatus.RATE_LIMITED:
      return "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300";
    case TargetStatus.IDLE:
      return "bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300";
  }
}

export default async function DashboardPage() {
  const [stats, targets] = await Promise.all([getStats(), getTargets()]);

  const cards = [
    {
      label: "Total Targets",
      value: stats.total_targets,
      href: "/dashboard/targets",
    },
    {
      label: "Active Sessions",
      value: stats.active_sessions,
      href: "/dashboard/live",
    },
    {
      label: "OTPs (24h)",
      value: stats.otps_captured_24h,
      href: "/dashboard/live",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Overview
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Monitoring status across targets, sessions, and captured codes.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.label}
            href={card.href}
            className="rounded-xl border border-zinc-200 bg-white p-5 transition-colors hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700"
          >
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              {card.label}
            </p>
            <p className="mt-1 text-3xl font-semibold text-zinc-900 dark:text-zinc-50">
              {card.value}
            </p>
          </Link>
        ))}
      </div>

      <section className="rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
            Recent Targets
          </h2>
          <Link
            href="/dashboard/targets"
            className="text-sm font-medium text-zinc-500 underline-offset-2 hover:text-zinc-900 hover:underline dark:text-zinc-400 dark:hover:text-zinc-50"
          >
            View all
          </Link>
        </div>

        {targets.length === 0 ? (
          <p className="px-5 py-8 text-sm text-zinc-500 dark:text-zinc-400">
            No targets yet.{" "}
            <Link
              href="/dashboard/targets"
              className="font-medium text-zinc-900 underline-offset-2 hover:underline dark:text-zinc-100"
            >
              Add your first target.
            </Link>
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {targets.map((target) => (
              <li
                key={target.id}
                className="flex items-center justify-between px-5 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {target.email}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {target.provider}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusBadgeClass(
                    target.status
                  )}`}
                >
                  {target.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
