"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import Button from "@/components/Button";
import ErrorState from "@/components/ErrorState";
import ForgotPasswordModal from "@/components/ForgotPasswordModal";
import { Lock, Mail, ArrowRight, Zap, CheckCircle2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, loading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [forgotModalOpen, setForgotModalOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid credentials. Please verify your details.");
    }
  };

  const handleFillDemo = () => {
    setEmail("investigator@truthscan.ai");
    setPassword("audit-neural-pass-2026");
    setSuccessMessage(null);
    setError(null);
  };

  return (
    <div className="max-w-md mx-auto my-8 sm:my-16 space-y-6">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <div className="w-14 h-14 bg-[#B7FF3C] border-2 border-[#111111] shadow-hard-xs mx-auto overflow-hidden flex items-center justify-center p-0.5">
          <img src="/image.png" alt="TruthScan AI Logo" className="w-full h-full object-cover" />
        </div>
        <h1 className="font-display text-3xl sm:text-4xl uppercase tracking-tight text-[#111111]">
          INVESTIGATOR LOGIN
        </h1>
        <p className="font-mono-tech text-xs text-[#111111]/70">
          Enter credentials to access telemetry logs and custom detection models.
        </p>
      </div>

      {successMessage && (
        <div className="border-2 border-[#111111] bg-[#B7FF3C] p-4 shadow-hard-sm flex items-start gap-2.5 animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-[#111111] shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-mono-tech text-xs font-bold uppercase text-[#111111]">
              CREDENTIALS UPDATED
            </div>
            <div className="font-mono-tech text-xs text-[#111111]/90">
              {successMessage}
            </div>
          </div>
        </div>
      )}

      {error && (
        <ErrorState
          title="LOGIN REJECTED"
          message={error}
          onRetry={() => setError(null)}
        />
      )}

      {/* Main Login Card */}
      <div className="border-3 border-[#111111] bg-white shadow-hard-lg p-6 sm:p-8 space-y-5">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Email */}
          <div className="space-y-1.5">
            <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" />
              <span>TERMINAL EMAIL</span>
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@domain.com"
              className="w-full p-2.5 font-mono-tech text-sm bg-[#F5F1E8]/50 border-2 border-[#111111] focus:outline-none focus:bg-white"
              disabled={loading}
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" />
                <span>ACCESS KEY</span>
              </label>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setSuccessMessage(null);
                  setForgotModalOpen(true);
                }}
                className="font-mono-tech text-[10px] text-[#111111]/60 hover:text-[#111111] underline cursor-pointer"
              >
                Forgot password?
              </button>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full p-2.5 font-mono-tech text-sm bg-[#F5F1E8]/50 border-2 border-[#111111] focus:outline-none focus:bg-white"
              disabled={loading}
            />
          </div>

          <div className="pt-2">
            <Button
              type="submit"
              variant="accent"
              size="md"
              loading={loading}
              className="w-full"
              icon={ArrowRight}
            >
              AUTHENTICATE SESSION
            </Button>
          </div>
        </form>

        {/* Demo Credentials */}
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
      </div>

      {/* Footer link */}
      <div className="text-center font-mono-tech text-xs text-[#111111]/80">
        Need a new clearance profile?{" "}
        <Link href="/register" className="font-bold text-[#111111] underline">
          CREATE ACCOUNT
        </Link>
      </div>

      {/* Forgot Password Modal */}
      <ForgotPasswordModal
        isOpen={forgotModalOpen}
        onClose={() => setForgotModalOpen(false)}
        initialEmail={email}
        onSuccess={(resetUserEmail) => {
          setEmail(resetUserEmail);
          setPassword("");
          setSuccessMessage("Password reset successfully! Please log in with your new access key.");
        }}
      />
    </div>
  );
}
