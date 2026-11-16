"use client";

import React, { useState, useEffect } from "react";
import Button from "@/components/Button";
import {
  X,
  Mail,
  KeyRound,
  Lock,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Eye,
  EyeOff,
  ShieldAlert,
} from "lucide-react";
import { forgotPassword, verifyResetOtp, resetPassword } from "@/lib/api";

export default function ForgotPasswordModal({
  isOpen,
  onClose,
  initialEmail = "",
  onSuccess,
}) {
  const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: New Password, 4: Success
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cooldown, setCooldown] = useState(0);

  // Sync initial email when modal opens
  useEffect(() => {
    if (isOpen) {
      if (initialEmail) setEmail(initialEmail);
      setStep(1);
      setOtp("");
      setNewPassword("");
      setConfirmPassword("");
      setError(null);
      setLoading(false);
    }
  }, [isOpen, initialEmail]);

  // Resend cooldown timer countdown
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  // Escape key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Step 1: Send Reset OTP
  const handleRequestOtp = async (e) => {
    if (e) e.preventDefault();
    setError(null);

    const cleanEmail = (email || "").trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Please provide a valid investigator email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await forgotPassword(cleanEmail);
      if (res && res.success === false) {
        throw new Error(res.message || "Failed to dispatch reset code.");
      }
      setStep(2);
      setCooldown(60);
    } catch (err) {
      setError(err.message || "Failed to dispatch reset code. Please verify your email.");
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify Reset OTP
  const handleVerifyOtp = async (e) => {
    if (e) e.preventDefault();
    setError(null);

    const cleanOtp = (otp || "").trim();
    if (cleanOtp.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setLoading(true);
    try {
      const res = await verifyResetOtp(email.trim().toLowerCase(), cleanOtp);
      if (res && res.success === false) {
        throw new Error(res.message || "Invalid or expired reset code.");
      }
      setStep(3);
    } catch (err) {
      setError(err.message || "Invalid or expired reset code. Please check your inbox or resend.");
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set New Password
  const handleResetPassword = async (e) => {
    if (e) e.preventDefault();
    setError(null);

    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Access keys do not match. Please re-enter.");
      return;
    }

    setLoading(true);
    try {
      const res = await resetPassword(
        email.trim().toLowerCase(),
        otp.trim(),
        newPassword
      );
      if (res && res.success === false) {
        throw new Error(res.message || "Failed to update password.");
      }
      setStep(4);
    } catch (err) {
      setError(err.message || "Failed to reset password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Resend OTP trigger
  const handleResend = async () => {
    if (cooldown > 0 || loading) return;
    setError(null);
    setLoading(true);
    try {
      const res = await forgotPassword(email.trim().toLowerCase());
      if (res && res.success === false) {
        throw new Error(res.message || "Failed to resend code.");
      }
      setCooldown(60);
    } catch (err) {
      setError(err.message || "Failed to resend code.");
    } finally {
      setLoading(false);
    }
  };

  const handleFinishSuccess = () => {
    if (onSuccess) onSuccess(email);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-md flex flex-col border-3 border-[#111111] bg-[#F5F1E8] shadow-hard-lg overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#111111] text-[#F5F1E8] border-b-2 border-[#111111]">
          <div className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-[#B7FF3C]" />
            <span className="font-display text-sm tracking-widest uppercase">
              RECOVER ACCESS KEY
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 border border-white/40 hover:bg-[#FF4D4D] hover:border-white transition-colors cursor-pointer text-white"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Progress Indicator */}
        <div className="grid grid-cols-3 bg-[#E8E2D5] border-b-2 border-[#111111] text-[10px] font-mono-tech uppercase font-bold text-center">
          <div
            className={`py-2 px-1 border-r border-[#111111] ${
              step === 1
                ? "bg-[#B7FF3C] text-[#111111]"
                : step > 1
                ? "bg-[#111111] text-white"
                : "text-[#111111]/60"
            }`}
          >
            1. EMAIL
          </div>
          <div
            className={`py-2 px-1 border-r border-[#111111] ${
              step === 2
                ? "bg-[#B7FF3C] text-[#111111]"
                : step > 2
                ? "bg-[#111111] text-white"
                : "text-[#111111]/60"
            }`}
          >
            2. VERIFY OTP
          </div>
          <div
            className={`py-2 px-1 ${
              step === 3 || step === 4
                ? "bg-[#B7FF3C] text-[#111111]"
                : "text-[#111111]/60"
            }`}
          >
            3. NEW PASS
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          {/* Error Banner */}
          {error && (
            <div className="p-3 bg-[#FF4D4D]/15 border-2 border-[#FF4D4D] text-[#111111] font-mono-tech text-xs flex items-start gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-[#FF4D4D] shrink-0 mt-0.5" />
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          {/* STEP 1: REQUEST OTP */}
          {step === 1 && (
            <form onSubmit={handleRequestOtp} className="space-y-4">
              <div className="space-y-1.5">
                <p className="font-mono-tech text-xs text-[#111111]/80 leading-relaxed">
                  Enter your registered investigator terminal email. We will dispatch a 6-digit reset code to verify your identity.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5" />
                  <span>REGISTERED EMAIL</span>
                </label>
                <input
                  type="email"
                  required
                  autoFocus
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@domain.com"
                  className="w-full p-2.5 font-mono-tech text-sm bg-white border-2 border-[#111111] focus:outline-none focus:bg-white shadow-hard-xs"
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
                  DISPATCH RESET OTP
                </Button>
              </div>
            </form>
          )}

          {/* STEP 2: VERIFY OTP */}
          {step === 2 && (
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <p className="font-mono-tech text-xs text-[#111111]/80">
                    Security code sent to:
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setStep(1);
                      setError(null);
                    }}
                    className="font-mono-tech text-[11px] font-bold text-[#111111] underline hover:text-[#B7FF3C] cursor-pointer"
                  >
                    Change
                  </button>
                </div>
                <div className="font-mono-tech text-xs font-bold text-[#111111] bg-white border border-[#111111] p-2 truncate">
                  {email}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>6-DIGIT VERIFICATION CODE</span>
                </label>
                <input
                  type="text"
                  required
                  autoFocus
                  maxLength={6}
                  value={otp}
                  onChange={(e) => {
                    const val = e.target.value.replace(/[^0-9]/g, "");
                    setOtp(val);
                  }}
                  placeholder="••••••"
                  className="w-full p-3 font-mono-tech text-center text-xl font-bold tracking-[0.4em] bg-white border-2 border-[#111111] focus:outline-none focus:bg-white shadow-hard-xs"
                  disabled={loading}
                />
                <p className="font-mono-tech text-[10px] text-[#111111]/70">
                  Code expires in 5 minutes. Check spam or terminal console if not visible.
                </p>
              </div>

              <div className="pt-2 space-y-2">
                <Button
                  type="submit"
                  variant="accent"
                  size="md"
                  loading={loading}
                  className="w-full"
                  icon={ArrowRight}
                >
                  VERIFY CODE
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    disabled={cooldown > 0 || loading}
                    onClick={handleResend}
                    className="font-mono-tech text-xs text-[#111111]/70 hover:text-[#111111] disabled:opacity-50 inline-flex items-center gap-1.5 cursor-pointer underline disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
                    <span>
                      {cooldown > 0 ? `Resend OTP in ${cooldown}s` : "Resend OTP Code"}
                    </span>
                  </button>
                </div>
              </div>
            </form>
          )}

          {/* STEP 3: SET NEW PASSWORD */}
          {step === 3 && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-1.5">
                <p className="font-mono-tech text-xs text-[#111111]/80 leading-relaxed">
                  Verification confirmed. Enter and confirm your new access password (minimum 6 characters).
                </p>
              </div>

              {/* New Password */}
              <div className="space-y-1.5">
                <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" />
                  <span>NEW ACCESS KEY</span>
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    autoFocus
                    minLength={6}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full p-2.5 pr-10 font-mono-tech text-sm bg-white border-2 border-[#111111] focus:outline-none focus:bg-white shadow-hard-xs"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#111111]/60 hover:text-[#111111] cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div className="space-y-1.5">
                <label className="font-mono-tech text-xs font-bold uppercase text-[#111111] flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5" />
                  <span>CONFIRM ACCESS KEY</span>
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full p-2.5 font-mono-tech text-sm bg-white border-2 border-[#111111] focus:outline-none focus:bg-white shadow-hard-xs"
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
                  icon={Lock}
                >
                  SAVE NEW ACCESS KEY
                </Button>
              </div>
            </form>
          )}

          {/* STEP 4: SUCCESS */}
          {step === 4 && (
            <div className="text-center py-4 space-y-4">
              <div className="w-16 h-16 bg-[#B7FF3C] border-3 border-[#111111] shadow-hard mx-auto flex items-center justify-center">
                <CheckCircle2 className="w-9 h-9 text-[#111111]" />
              </div>

              <div className="space-y-1.5">
                <h3 className="font-display text-xl uppercase tracking-tight text-[#111111]">
                  ACCESS KEY UPDATED
                </h3>
                <p className="font-mono-tech text-xs text-[#111111]/80 max-w-xs mx-auto leading-relaxed">
                  Your password has been securely reset. You can now log into your investigator terminal with your new credentials.
                </p>
              </div>

              <div className="pt-2">
                <Button
                  type="button"
                  variant="accent"
                  size="md"
                  className="w-full"
                  onClick={handleFinishSuccess}
                  icon={ArrowRight}
                >
                  PROCEED TO LOGIN
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
