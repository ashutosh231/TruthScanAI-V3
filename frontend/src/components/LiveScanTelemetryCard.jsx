"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Wifi, ChevronDown } from "lucide-react";

export default function LiveScanTelemetryCard() {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse((p) => !p);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  // Histogram heights replicating the background telemetry in the reference image
  const histogramBars = [
    12, 14, 18, 22, 16, 20, 24, 28, 35, 45, 62, 85, 96, 78, 64, 48, 36, 28, 22, 18,
  ];

  return (
    <div className="relative w-full max-w-lg mx-auto lg:max-w-none pt-2 pb-8 sm:pb-10">
      {/* ============================================================== */}
      {/* MAIN TELEMETRY CARD (Dark Rounded Futuristic Cockpit)          */}
      {/* ============================================================== */}
      <div className="relative rounded-[2.5rem] border-3 border-[#111111] bg-[#0E1217] shadow-hard-lg overflow-hidden p-6 sm:p-7 text-white select-none">
        {/* Subtle Tech Coordinate Grid Background */}
        <div
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px)",
            backgroundSize: "22px 22px",
          }}
        />

        {/* Ambient Top Glow */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-64 h-32 bg-[#B7FF3C]/10 rounded-full blur-3xl pointer-events-none" />

        {/* ------------------------------------------------------------ */}
        {/* TOP STATUS BAR                                               */}
        {/* ------------------------------------------------------------ */}
        <div className="relative z-10 flex items-center justify-between pb-4">
          {/* Live Scan Indicator */}
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#B7FF3C] inline-block shadow-[0_0_10px_#B7FF3C] animate-pulse" />
            <span className="font-mono-tech text-xs sm:text-sm font-bold tracking-wider text-[#B7FF3C]">
              LIVE SCAN
            </span>
          </div>

          {/* Version & Signal Status */}
          <div className="flex items-center gap-2 font-mono-tech text-xs text-[#E8E2D5]/60">
            <span className="tracking-wider">v3.1.0</span>
            <div className="p-1 rounded-md bg-white/5 border border-white/10 text-[#B7FF3C] flex items-center justify-center">
              <Wifi className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* SECONDARY HUD CONTROLS                                       */}
        {/* ------------------------------------------------------------ */}
        <div className="relative z-10 flex items-center justify-between text-[10px] font-mono-tech text-[#E8E2D5]/50 pb-2">
          <div className="flex items-center gap-1 hover:text-white transition-colors cursor-pointer">
            <span>DAYS USING MEDIAN</span>
            <ChevronDown className="w-3 h-3" />
          </div>
          <div className="hidden sm:flex items-center gap-3">
            <span>OPTIONS</span>
            <span>START RENDER VS BOUNCE RATE</span>
          </div>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* VISUAL CHART AREA WITH CENTRAL 94 CREDIBILITY GAUGE          */}
        {/* ------------------------------------------------------------ */}
        <div className="relative z-10 my-4 h-44 sm:h-52 flex items-center justify-center overflow-hidden">
          {/* Background SVG Grid & Histogram Chart */}
          <div className="absolute inset-0 flex items-end justify-between px-2 gap-1.5 opacity-60">
            {histogramBars.map((heightPct, idx) => (
              <div
                key={idx}
                className="w-full rounded-t-sm transition-all duration-700"
                style={{
                  height: `${heightPct}%`,
                  background:
                    idx >= 10 && idx <= 15
                      ? "linear-gradient(to top, rgba(20, 184, 166, 0.4), rgba(45, 212, 191, 0.95))"
                      : "linear-gradient(to top, rgba(19, 78, 74, 0.2), rgba(20, 184, 166, 0.45))",
                }}
              />
            ))}
          </div>

          {/* Undulating Pink Trend Line (SVG) */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none opacity-70"
            preserveAspectRatio="none"
            viewBox="0 0 300 120"
          >
            <path
              d="M0,75 Q30,68 60,78 T120,70 T180,62 T240,76 T300,74"
              fill="none"
              stroke="#F43F5E"
              strokeWidth="2"
            />
          </svg>

          {/* Secondary Bounce Rate Tag in background */}
          <div className="absolute left-2 top-8 p-1.5 bg-black/40 border border-white/10 text-[9px] font-mono-tech text-white/50">
            <div>Bounce Rate</div>
            <div className="text-white font-bold text-xs">7.1%</div>
          </div>

          {/* ---------------------------------------------------------- */}
          {/* CENTERPIECE: CIRCULAR 94 CREDIBILITY HUD GAUGE             */}
          {/* ---------------------------------------------------------- */}
          <div className="relative z-20 flex flex-col items-center justify-center">
            {/* Outer Concentric Radar Rings with Ticks */}
            <div className="relative w-32 h-32 sm:w-36 sm:h-36 rounded-full border-2 border-[#B7FF3C] flex items-center justify-center shadow-[0_0_24px_rgba(183,255,60,0.25)] bg-[#0E1217]/90 backdrop-blur-md">
              {/* Outer Dashed Orbit Ring */}
              <div className="absolute -inset-2.5 rounded-full border border-dashed border-[#B7FF3C]/50 animate-[spin_24s_linear_infinite]" />

              {/* Crosshair Horizontal Line */}
              <div className="absolute left-0 right-0 h-[1px] bg-[#B7FF3C]/40" />

              {/* Crosshair Ticks */}
              <div className="absolute -top-1 w-2 h-1 bg-[#B7FF3C]" />
              <div className="absolute -bottom-1 w-2 h-1 bg-[#B7FF3C]" />
              <div className="absolute -left-1 w-1 h-2 bg-[#B7FF3C]" />
              <div className="absolute -right-1 w-1 h-2 bg-[#B7FF3C]" />

              {/* Inside Gauge Text */}
              <div className="text-center space-y-0.5">
                <div className="font-display text-4xl sm:text-5xl font-extrabold text-[#B7FF3C] leading-none tracking-tight drop-shadow-[0_2px_8px_rgba(183,255,60,0.5)]">
                  94
                </div>
                <div className="font-mono-tech text-[9px] sm:text-[10px] font-bold text-[#E8E2D5] tracking-widest uppercase">
                  CREDIBILITY
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* METRICS & PROGRESS GAUGES                                    */}
        {/* ------------------------------------------------------------ */}
        <div className="relative z-10 space-y-3 font-mono-tech text-xs pt-1">
          {/* Source Trust */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="text-[#E8E2D5]/70 font-semibold tracking-wider">
                SOURCE TRUST
              </span>
              <span className="text-[#B7FF3C] font-bold">92%</span>
            </div>
            <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden p-[1px]">
              <div className="h-full bg-[#B7FF3C] rounded-full w-[92%] shadow-[0_0_8px_#B7FF3C]" />
            </div>
          </div>

          {/* Factual Accuracy */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="text-[#E8E2D5]/70 font-semibold tracking-wider">
                FACTUAL ACCURACY
              </span>
              <span className="text-[#B7FF3C] font-bold">88%</span>
            </div>
            <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden p-[1px]">
              <div className="h-full bg-[#B7FF3C] rounded-full w-[88%] shadow-[0_0_8px_#B7FF3C]" />
            </div>
          </div>

          {/* Bias Detection */}
          <div className="flex justify-between items-center text-[11px] pt-1 border-t border-white/10">
            <span className="text-[#E8E2D5]/70 tracking-wider">BIAS DETECTION</span>
            <span className="text-[#B7FF3C] font-bold">LOW</span>
          </div>

          {/* Emotion / Manipulation Detection */}
          <div className="flex justify-between items-center text-[10px] text-white/50 pt-0.5">
            <div className="flex items-center gap-1.5">
              <span>PTIONS [ON]</span>
              <div className="w-8 h-1 bg-[#FF4D4D] rounded-full" />
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#FF4D4D] font-bold tracking-wider">DETECTED</span>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------ */}
        {/* BOTTOM TELEMETRY FOOTER                                      */}
        {/* ------------------------------------------------------------ */}
        <div className="relative z-10 flex items-end justify-between pt-4 mt-2 border-t border-white/10 font-mono-tech">
          <div className="space-y-0.5">
            <div className="text-sm sm:text-base font-bold text-white tracking-tight">
              479K
            </div>
            <div className="text-[10px] text-[#E8E2D5]/50">Sessions • 4 pvs</div>
          </div>

          <div className="space-y-0.5 text-center">
            <div className="text-sm sm:text-base font-bold text-white tracking-tight">
              17min
            </div>
            <div className="text-[10px] text-[#E8E2D5]/50">Session Length</div>
          </div>

          {/* Animated Audio / Equalizer Bars */}
          <div className="flex items-end gap-1 h-5 pb-0.5">
            <span className="w-1 bg-[#B7FF3C] rounded-full animate-[pulse_1.2s_ease-in-out_infinite] h-2.5" />
            <span className="w-1 bg-[#B7FF3C] rounded-full animate-[pulse_0.9s_ease-in-out_infinite] h-4" />
            <span className="w-1 bg-[#B7FF3C] rounded-full animate-[pulse_1.5s_ease-in-out_infinite] h-5" />
            <span className="w-1 bg-[#B7FF3C] rounded-full animate-[pulse_1.1s_ease-in-out_infinite] h-3.5" />
            <span className="w-1 bg-[#B7FF3C] rounded-full animate-[pulse_1.3s_ease-in-out_infinite] h-2" />
          </div>
        </div>
      </div>

      {/* ============================================================== */}
      {/* OVERLAPPING VIBRANT LIME STICKER CARD (MULTI-MODEL AI)         */}
      {/* ============================================================== */}
      <div className="relative mt-4 sm:mt-6 lg:mt-0 lg:absolute lg:-bottom-4 lg:-left-6 z-20 w-full sm:w-80 border-3 border-[#111111] bg-[#B7FF3C] p-5 shadow-hard-lg space-y-3 transform lg:-rotate-1 hover:rotate-0 transition-transform">
        {/* Header with Sparkles icon & title */}
        <div className="flex items-start gap-2.5">
          <Sparkles className="w-6 h-6 text-[#111111] shrink-0 mt-0.5" />
          <h3 className="font-display text-2xl sm:text-3xl font-black uppercase tracking-tight text-[#111111] leading-none">
            MULTI-MODEL AI
          </h3>
        </div>

        {/* Descriptive Body */}
        <p className="font-mono-tech text-xs sm:text-[13px] text-[#111111] leading-relaxed font-semibold">
          Real-time NLP analysis, deepfake detection, source verification, emotional manipulation detection, and credibility scoring.
        </p>

        {/* Divider */}
        <div className="border-b-2 border-[#111111] pt-1" />

        {/* Footer Details */}
        <div className="flex items-center justify-between font-mono-tech text-xs font-bold text-[#111111] pt-0.5">
          <span>v3.1 ENSEMBLE</span>
          {/* Four dots matching the image */}
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#111111]" />
            <span className="w-2 h-2 rounded-full bg-[#111111]" />
            <span className="w-2 h-2 rounded-full bg-[#111111]" />
            <span className="w-2 h-2 rounded-full bg-[#111111]" />
          </div>
        </div>
      </div>
    </div>
  );
}
