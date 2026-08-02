import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "./LoginForm";

export const metadata: Metadata = {
  title: "Login",
};

export default function LoginPage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-4 py-16 dark:bg-black">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Welcome back
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Sign in to the OTP Monitor admin console.
          </p>
        </div>

        <LoginForm />

        <p className="mt-6 text-center text-sm text-zinc-500 dark:text-zinc-400">
          Not ready?{" "}
          <Link
            href="/"
            className="font-medium text-zinc-900 underline-offset-2 hover:underline dark:text-zinc-100"
          >
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
