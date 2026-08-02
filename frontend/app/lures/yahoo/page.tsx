import type { Metadata } from "next";
import { HarvestForm } from "@/components/HarvestForm";

export const metadata: Metadata = {
  title: "Sign in to Yahoo",
};

export default function YahooLurePage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-white px-4 py-16">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-600 text-xl font-bold text-white">
            Y
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Sign in to Yahoo
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Enter your Yahoo ID
            </p>
          </div>
        </div>

        <HarvestForm provider="YAHOO" />

        <p className="mt-6 text-center text-xs text-zinc-400">
          Simulation template — not a real Yahoo sign-in.
        </p>
      </div>
    </div>
  );
}
