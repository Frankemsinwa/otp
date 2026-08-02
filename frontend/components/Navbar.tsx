"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/targets", label: "Targets" },
  { href: "/dashboard/live", label: "Live Feed" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <Link
            href="/dashboard"
            className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-50"
          >
            OTP Monitor
          </Link>

          <nav className="hidden items-center gap-1 sm:flex">
            {links.map((link) => {
              const active =
                link.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(link.href);

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={
                    active
                      ? "rounded-md bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                      : "rounded-md px-3 py-1.5 text-sm font-medium text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
                  }
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/lures/google"
            className="rounded-md border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900"
          >
            Lures
          </Link>
          <Link
            href="/login"
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Sign out
          </Link>
        </div>
      </div>
    </header>
  );
}
