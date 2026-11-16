"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { adminLogin } from "@/lib/api";
import Button from "@/components/Button";
import ErrorState from "@/components/ErrorState";
import { ShieldCheck, Lock, Mail, ArrowRight, Zap, Shield } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (isAdminMode) {
      // Admin login flow
      setAdminLoading(true);
      try {
        const res = await adminLogin({ email, password });
        if (res?.data?.accessToken) {
          const token = res.data.accessToken;
          const userObj = res.data.user;
          const userStr = JSON.stringify(userObj);
          sessionStorage.setItem("truthscan_admin_token", token);
          sessionStorage.setItem("truthscan_admin_user", userStr);
          localStorage.setItem("truthscan_admin_token", token);
          localStorage.setItem("truthscan_admin_user", userStr);

          // Keep user session in sync so full client knows admin role across all pages
          sessionStorage.setItem("truthscan_access_token", token);
          sessionStorage.setItem("truthscan_user_session", userStr);
          localStorage.setItem("truthscan_access_token", token);
          localStorage.setItem("truthscan_user_session", userStr);

          router.push("/admin");
        } else {
          setError(res?.message || "Admin authentication failed.");
        }
      } catch (err) {
        setError(err.message || "Admin credentials rejected. Access denied.");
      } finally {
        setAdminLoading(false);
      }
    } else {
      // Regular user login
      try {
        await login({ email, password });
        router.push("/dashboard");
      } catch (err) {
        setError(err.message || "Invalid credentials. Please verify your details.");
      }
    }
  };

  const handleFillDemo = () => {
    setEmail("investigator@truthscan.ai");
    setPassword("audit-neural-pass-2026");
  };

  const toggleAdminMode = () => {
    setIsAdminMode((prev) => !prev);
    setError(null);
    setEmail("");
    setPassword("");
  };

  const isLoading = isAdminMode ? adminLoading : loading;

  return (
    <div className="max-w-md mx-auto my-8 sm:my-16 space-y-6">
      {/* Admin Mode Badge */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={toggleAdminMode}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 border-2 border-[#111111] font-mono-tech text-[11px] font-bold uppercase transition-all cursor-pointer shadow-[2px_2px_0px_0px_#111111] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] ${
            isAdminMode
              ? "bg-[#111111] text-[#B7FF3C]"
              : "bg-[#F5F1E8] text-[#111111] hover:bg-[#B7FF3C]"
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          {isAdminMode ? "← BACK TO USER LOGIN" : "ADMIN LOGIN"}
        </button>
      </div>

      {/* Brand Header */}
      <div className="text-center space-y-2">
        <div
          className={`w-14 h-14 border-2 border-[#111111] shadow-hard-xs mx-auto overflow-hidden flex items-center justify-center p-0.5 transition-colors ${
            isAdminMode ? "bg-[#111111]" : "bg-[#B7FF3C]"
          }`}
        >
          {isAdminMode ? (
            <Shield className="w-7 h-7 text-[#B7FF3C]" />
          ) : (
            <img src="/image.png" alt="TruthScan AI Logo" className="w-full h-full object-cover" />
          )}
        </div>
        <h1 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111]">
          {isAdminMode ? "ADMIN CLEARANCE" : "INVESTIGATOR LOGIN"}
        </h1>
        <p className="font-mono-tech text-xs text-[#111111]/70">
          {isAdminMode
            ? "Restricted access. Authorised personnel only."
            : "Enter credentials to access telemetry logs and custom detection models."}
        </p>
        {isAdminMode && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#111111] border-2 border-[#111111]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#B7FF3C]" />
            <span className="font-mono-tech text-[10px] font-bold text-[#B7FF3C] uppercase tracking-widest">
              ADMIN PORTAL
            </span>
          </div>
        )}
      </div>

      {error && (
        <ErrorState
          title={isAdminMode ? "ACCESS DENIED" : "LOGIN REJECTED"}
          message={error}
          onRetry={() => setError(null)}
        />
      )}

      {/* Main Login Card */}
      <div
        className={`border-3 border-[#111111] bg-white shadow-hard-lg p-6 sm:p-8 space-y-5 transition-all ${
          isAdminMode ? "border-[#111111] shadow-[6px_6px_0px_0px_#111111]" : ""
        }`}
      >
        {/* Admin mode stripe */}
        {isAdminMode && (
          <div className="flex items-center gap-2 bg-[#111111] -mx-6 sm:-mx-8 -mt-6 sm:-mt-8 px-6 py-2 mb-4">
            <Lock className="w-3.5 h-3.5 text-[#B7FF3C]" />
            <span className="font-mono-tech text-[11px] font-bold uppercase text-[#B7FF3C] tracking-widest">
              SECURE ADMIN CHANNEL — ENCRYPTED
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div className="space-y-1.5">
            <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" />
              <span>{isAdminMode ? "ADMIN EMAIL" : "TERMINAL EMAIL"}</span>
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={isAdminMode ? "admin@domain.com" : "analyst@domain.com"}
              className="w-full p-2.5 font-mono-tech text-sm bg-[#F5F1E8]/50 border-2 border-[#111111] focus:outline-none focus:bg-white"
              disabled={isLoading}
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                <span>{isAdminMode ? "ADMIN KEY" : "ACCESS KEY"}</span>
              </label>
              {!isAdminMode && (
                <button
                  type="button"
                  onClick={() => alert("Password reset token dispatched to terminal administrator.")}
                  className="font-mono-tech text-[10px] text-[#111111]/60 hover:text-[#111111] underline cursor-pointer"
                >
                  Forgot password?
                </button>
              )}
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full p-2.5 font-mono-tech text-sm bg-[#F5F1E8]/50 border-2 border-[#111111] focus:outline-none focus:bg-white"
              disabled={isLoading}
            />
          </div>

          <div className="pt-2">
            {isAdminMode ? (
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 bg-[#111111] text-[#B7FF3C] font-display text-sm uppercase tracking-wide px-6 py-3 border-2 border-[#111111] shadow-[4px_4px_0px_0px_#B7FF3C] hover:shadow-none hover:translate-x-[4px] hover:translate-y-[4px] transition-all disabled:opacity-60 cursor-pointer"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#B7FF3C] border-t-transparent" />
                    AUTHENTICATING...
                  </span>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    VERIFY ADMIN IDENTITY
                  </>
                )}
              </button>
            ) : (
              <Button
                type="submit"
                variant="accent"
                size="md"
                loading={isLoading}
                className="w-full"
                icon={ArrowRight}
              >
                AUTHENTICATE SESSION
              </Button>
            )}
          </div>
        </form>

        {/* Demo Credentials (user mode only) */}
        {!isAdminMode && (
          <div className="pt-3 border-t-2 border-[#111111] text-center">
            <button
              type="button"
              onClick={handleFillDemo}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#E8E2D5] hover:bg-[#B7FF3C] border-2 border-[#111111] font-mono-tech text-xs font-bold uppercase transition-colors cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5 text-[#111111]" />
              <span>AUTOFILL DEMO CREDENTIALS</span>
            </button>
          </div>
        )}
      </div>

      {/* Footer link */}
      {!isAdminMode && (
        <div className="text-center font-mono-tech text-xs text-[#111111]/80">
          Need a new clearance profile?{" "}
          <Link href="/register" className="font-bold text-[#111111] underline">
            CREATE ACCOUNT
          </Link>
        </div>
      )}
    </div>
  );
}
