import type { Metadata } from "next";
import { TargetList } from "./TargetList";

export const metadata: Metadata = {
  title: "Targets",
};

export default function TargetsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Targets
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Manage email target profiles and their monitoring status.
        </p>
      </div>

      <TargetList />
    </div>
  );
}
