"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

const links = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/otps", label: "Captured OTPs" },
  { href: "/dashboard/targets", label: "Targets" },
  { href: "/dashboard/live", label: "Live Feed" },
];

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Close drawer on route change
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const isActive = (href: string) =>
    href === "/dashboard"
      ? pathname === "/dashboard"
      : pathname.startsWith(href);

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          {/* Left: Logo + desktop nav */}
          <div className="flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-50"
            >
              OTP Monitor
            </Link>

            {/* Desktop nav — hidden on mobile */}
            <nav className="hidden items-center gap-1 sm:flex">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={
                    isActive(link.href)
                      ? "rounded-md bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                      : "rounded-md px-3 py-1.5 text-sm font-medium text-zinc-500 transition-colors hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
                  }
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Right: actions + hamburger */}
          <div className="flex items-center gap-2">
            <Link
              href="/lures/google"
              className="hidden rounded-md border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900 sm:inline-flex"
            >
              Lures
            </Link>
            <Link
              href="/login"
              className="hidden rounded-md bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200 sm:inline-flex"
            >
              Sign out
            </Link>

            {/* Hamburger — only on mobile */}
            <button
              type="button"
              onClick={() => setOpen((o) => !o)}
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              className="flex h-9 w-9 flex-col items-center justify-center gap-1.5 rounded-md transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 sm:hidden"
            >
              {/* Three bar → X animation */}
              <span
                className={`block h-0.5 w-5 rounded-full bg-zinc-700 transition-all duration-300 dark:bg-zinc-300 ${
                  open ? "translate-y-2 rotate-45" : ""
                }`}
              />
              <span
                className={`block h-0.5 w-5 rounded-full bg-zinc-700 transition-all duration-300 dark:bg-zinc-300 ${
                  open ? "opacity-0" : ""
                }`}
              />
              <span
                className={`block h-0.5 w-5 rounded-full bg-zinc-700 transition-all duration-300 dark:bg-zinc-300 ${
                  open ? "-translate-y-2 -rotate-45" : ""
                }`}
              />
            </button>
          </div>
        </div>

        {/* Mobile dropdown drawer */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out sm:hidden ${
            open ? "max-h-96 border-t border-zinc-200 dark:border-zinc-800" : "max-h-0"
          }`}
        >
          <nav className="flex flex-col px-4 py-3 gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
                    : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-50"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="my-1 border-t border-zinc-100 dark:border-zinc-800" />
            <Link
              href="/lures/google"
              className="rounded-md px-3 py-2.5 text-sm font-medium text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-50 transition-colors"
            >
              Lures
            </Link>
            <Link
              href="/login"
              className="rounded-md bg-zinc-900 px-3 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Sign out
            </Link>
          </nav>
        </div>
      </header>

      {/* Backdrop — tap outside to close */}
      {open && (
        <div
          className="fixed inset-0 z-20 sm:hidden"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}
    </>
  );
}
