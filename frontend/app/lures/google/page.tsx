import type { Metadata } from "next";
import { HarvestForm } from "@/components/HarvestForm";

export const metadata: Metadata = {
  title: "Sign in — Google Account",
};

export default function GoogleLurePage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-white px-4 py-16">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-200 dark:border-zinc-800">
            <span className="text-xl font-semibold">G</span>
          </div>
          <div>
            <h1 className="text-2xl font-normal tracking-tight text-zinc-900 dark:text-zinc-50">
              Sign in
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Use your Google Account
            </p>
          </div>
        </div>

        <HarvestForm provider="GMAIL" />

        <p className="mt-6 text-center text-xs text-zinc-400">
          Simulation template — not a real Google sign-in.
        </p>
      </div>
    </div>
  );
}
