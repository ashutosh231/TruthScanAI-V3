"use client";

import React, { useState } from "react";

// Neo-Brutalist colour palette
const C = {
  bg: "#FFFFFF",
  cream: "#F5F1E8",
  border: "#111111",
  accent: "#B7FF3C",
  text: "#111111",
  muted: "#666666",
  grid: "#E2DCD0",
  verified: "#22C55E",
  false: "#EF4444",
  misleading: "#F59E0B",
  uncertain: "#8B5CF6",
  total: "#111111",
  purple: "#7C3AED",
  blue: "#2563EB",
  amber: "#D97706",
};

// ============================================================================
// 1. Line Chart: Fact Checks Over Time
// ============================================================================
export function FactChecksLineChart({ data = [] }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-xs font-mono-tech text-[#111111]/50 border-2 border-dashed border-[#111111]/30">
        NO AUDIT RECORDS FOR THIS PERIOD
      </div>
    );
  }

  const width = 640;
  const height = 220;
  const padLeft = 36;
  const padRight = 16;
  const padTop = 16;
  const padBottom = 32;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const maxVal = Math.max(1, ...data.map((d) => Math.max(d.total || 0, d.verified || 0, d.false || 0, d.misleading || 0)));

  const getX = (idx) => padLeft + (idx / Math.max(1, data.length - 1)) * chartW;
  const getY = (val) => padTop + chartH - (val / maxVal) * chartH;

  const createPath = (key) =>
    data.map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(d[key] || 0)}`).join(" ");

  const createAreaPath = (key) => {
    const line = createPath(key);
    return `${line} L ${getX(data.length - 1)} ${padTop + chartH} L ${getX(0)} ${padTop + chartH} Z`;
  };

  return (
    <div className="relative w-full">
      {/* Legend Header */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs font-mono-tech font-bold uppercase">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 border border-[#111111]" style={{ backgroundColor: C.total }} />
            Total
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 border border-[#111111]" style={{ backgroundColor: C.verified }} />
            Verified
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 border border-[#111111]" style={{ backgroundColor: C.false }} />
            False
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 border border-[#111111]" style={{ backgroundColor: C.misleading }} />
            Misleading
          </span>
        </div>
        <span className="font-mono-tech text-[10px] text-[#111111]/60">Peak: {maxVal}</span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible select-none">
        <defs>
          <linearGradient id="totalGradBrut" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.4" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Background Canvas */}
        <rect x={padLeft} y={padTop} width={chartW} height={chartH} fill={C.cream} />

        {/* Horizontal Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = padTop + chartH * (1 - pct);
          const v = Math.round(maxVal * pct);
          return (
            <g key={i}>
              <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke={C.grid} strokeWidth="1" strokeDasharray="3 3" />
              <text x={padLeft - 6} y={y + 3.5} textAnchor="end" fill={C.muted} fontSize="9" fontFamily="monospace">
                {v}
              </text>
            </g>
          );
        })}

        {/* Shaded Area for Total */}
        <path d={createAreaPath("total")} fill="url(#totalGradBrut)" />

        {/* Lines */}
        <path d={createPath("total")} fill="none" stroke={C.total} strokeWidth="2.5" strokeLinecap="round" />
        <path d={createPath("verified")} fill="none" stroke={C.verified} strokeWidth="2" strokeLinecap="round" />
        <path d={createPath("false")} fill="none" stroke={C.false} strokeWidth="2" strokeLinecap="round" />
        <path d={createPath("misleading")} fill="none" stroke={C.misleading} strokeWidth="2" strokeLinecap="round" />

        {/* Outer Frame */}
        <rect x={padLeft} y={padTop} width={chartW} height={chartH} fill="none" stroke={C.border} strokeWidth="1.5" />

        {/* Hover Points & Vertical Cursor */}
        {data.map((d, i) => {
          const x = getX(i);
          const isHovered = hoveredIdx === i;
          return (
            <g key={i} className="cursor-pointer" onMouseEnter={() => setHoveredIdx(i)} onMouseLeave={() => setHoveredIdx(null)}>
              {isHovered && (
                <line x1={x} y1={padTop} x2={x} y2={padTop + chartH} stroke={C.border} strokeWidth="1" strokeDasharray="2 2" />
              )}
              <circle cx={x} cy={getY(d.total || 0)} r={isHovered ? 5 : 3} fill={C.accent} stroke={C.border} strokeWidth="1.5" />
              <rect x={x - 8} y={padTop} width="16" height={chartH} fill="transparent" />
            </g>
          );
        })}

        {/* X-axis labels */}
        {data.map((d, i) => {
          if (data.length > 8 && i % Math.ceil(data.length / 6) !== 0 && i !== data.length - 1) return null;
          const x = getX(i);
          const parts = (d.date || "").split("-");
          const label = parts.length === 3 ? `${parts[1]}/${parts[2]}` : d.date;
          return (
            <text key={i} x={x} y={height - 8} textAnchor="middle" fill={C.muted} fontSize="9" fontFamily="monospace">
              {label}
            </text>
          );
        })}
      </svg>

      {/* Hover Tooltip Box */}
      {hoveredIdx !== null && data[hoveredIdx] && (
        <div
          className="pointer-events-none absolute z-20 border-2 border-[#111111] bg-white p-2.5 text-xs shadow-[3px_3px_0px_0px_#111111]"
          style={{
            left: `${Math.min(75, Math.max(5, (hoveredIdx / data.length) * 100))}%`,
            top: "10px",
          }}
        >
          <div className="mb-1 font-display text-[11px] uppercase font-bold text-[#111111]">{data[hoveredIdx].date}</div>
          <div className="space-y-0.5 font-mono-tech text-[10px]">
            <div className="flex justify-between gap-3 text-[#111111]"><span>Total:</span> <span className="font-bold">{data[hoveredIdx].total}</span></div>
            <div className="flex justify-between gap-3" style={{ color: C.verified }}><span>Verified:</span> <span className="font-bold">{data[hoveredIdx].verified}</span></div>
            <div className="flex justify-between gap-3" style={{ color: C.false }}><span>False:</span> <span className="font-bold">{data[hoveredIdx].false}</span></div>
            <div className="flex justify-between gap-3" style={{ color: C.misleading }}><span>Misleading:</span> <span className="font-bold">{data[hoveredIdx].misleading}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 2. Donut Chart: Verdict Distribution (Completely self-contained, no overflow)
// ============================================================================
export function VerdictDonutChart({ data = [] }) {
  const [hoveredSlice, setHoveredSlice] = useState(null);

  const total = data.reduce((acc, curr) => acc + (curr.value || 0), 0);

  if (total === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-xs font-mono-tech text-[#111111]/50 border-2 border-dashed border-[#111111]/30">
        NO VERDICT RECORDS
      </div>
    );
  }

  // Dimension settings (compact SVG that never bleeds out of card)
  const size = 150;
  const center = size / 2;
  const radius = 54;
  const strokeW = 20;
  const circumference = 2 * Math.PI * radius;

  let accumulated = 0;
  const slices = data.map((item) => {
    const pct = item.value / total;
    const strokeDasharray = `${pct * circumference} ${circumference}`;
    const strokeDashoffset = -accumulated * circumference;
    accumulated += pct;
    return { ...item, pct: Math.round(pct * 100), strokeDasharray, strokeDashoffset };
  });

  return (
    <div className="flex flex-col items-center justify-center gap-3 w-full overflow-hidden">
      {/* Centered Donut Ring */}
      <div className="relative flex items-center justify-center shrink-0">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90 select-none">
          {/* Base track */}
          <circle cx={center} cy={center} r={radius} fill="none" stroke={C.grid} strokeWidth={strokeW} />
          {/* Colored slices */}
          {slices.map((slice, i) => (
            <circle
              key={i}
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke={slice.color}
              strokeWidth={hoveredSlice === i ? strokeW + 4 : strokeW}
              strokeDasharray={slice.strokeDasharray}
              strokeDashoffset={slice.strokeDashoffset}
              strokeLinecap="butt"
              className="cursor-pointer transition-all duration-200"
              onMouseEnter={() => setHoveredSlice(i)}
              onMouseLeave={() => setHoveredSlice(null)}
            />
          ))}
          {/* Outer & Inner border rings for Neo-Brutalist look */}
          <circle cx={center} cy={center} r={radius + strokeW / 2} fill="none" stroke={C.border} strokeWidth="1.5" />
          <circle cx={center} cy={center} r={radius - strokeW / 2} fill="none" stroke={C.border} strokeWidth="1.5" />
        </svg>

        {/* Center Metric */}
        <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none">
          <span className="font-display text-2xl font-black tracking-tight text-[#111111] leading-none">{total}</span>
          <span className="font-mono-tech text-[8px] uppercase tracking-wider text-[#111111]/70 mt-0.5">VERDICTS</span>
        </div>
      </div>

      {/* Responsive 2x2 Grid Legend - 100% inside card bounds */}
      <div className="grid grid-cols-2 gap-1.5 w-full">
        {slices.map((slice, i) => (
          <div
            key={i}
            onMouseEnter={() => setHoveredSlice(i)}
            onMouseLeave={() => setHoveredSlice(null)}
            className={`flex items-center justify-between border-2 px-2 py-1 transition-all cursor-pointer ${
              hoveredSlice === i
                ? "border-[#111111] bg-[#B7FF3C] shadow-hard-xs"
                : "border-[#111111]/30 bg-[#F5F1E8] hover:border-[#111111]"
            }`}
          >
            <div className="flex items-center gap-1.5 overflow-hidden">
              <span
                className="h-2.5 w-2.5 border border-[#111111] shrink-0"
                style={{ backgroundColor: slice.color }}
              />
              <span className="font-mono-tech text-[10px] font-bold uppercase truncate text-[#111111]">
                {slice.name}
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0 ml-1">
              <span className="font-mono-tech text-[11px] font-black text-[#111111]">{slice.value}</span>
              <span className="font-mono-tech text-[9px] text-[#111111]/60">({slice.pct}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// 3. Area Chart: User Growth Over Time
// ============================================================================
export function UserGrowthAreaChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-xs font-mono-tech text-[#111111]/50 border-2 border-dashed border-[#111111]/30">
        NO REGISTRATION DATA
      </div>
    );
  }

  const width = 500;
  const height = 180;
  const padLeft = 32;
  const padRight = 16;
  const padTop = 16;
  const padBottom = 28;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const maxUsers = Math.max(1, ...data.map((d) => d.totalUsers || 0));

  const getX = (idx) => padLeft + (idx / Math.max(1, data.length - 1)) * chartW;
  const getY = (val) => padTop + chartH - (val / maxUsers) * chartH;

  const linePath = data.map((d, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(d.totalUsers || 0)}`).join(" ");
  const areaPath = `${linePath} L ${getX(data.length - 1)} ${padTop + chartH} L ${getX(0)} ${padTop + chartH} Z`;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none">
        <defs>
          <linearGradient id="userGrowthBrut" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.45" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Canvas */}
        <rect x={padLeft} y={padTop} width={chartW} height={chartH} fill={C.cream} />

        {/* Grid lines */}
        {[0, 0.5, 1].map((pct, i) => {
          const y = padTop + chartH * (1 - pct);
          return (
            <g key={i}>
              <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke={C.grid} strokeWidth="1" strokeDasharray="3 3" />
              <text x={padLeft - 6} y={y + 3.5} textAnchor="end" fill={C.muted} fontSize="9" fontFamily="monospace">
                {Math.round(maxUsers * pct)}
              </text>
            </g>
          );
        })}

        <path d={areaPath} fill="url(#userGrowthBrut)" />
        <path d={linePath} fill="none" stroke={C.border} strokeWidth="2.5" strokeLinecap="round" />

        {data.map((d, i) => (
          <circle key={i} cx={getX(i)} cy={getY(d.totalUsers || 0)} r="3" fill={C.accent} stroke={C.border} strokeWidth="1.5" />
        ))}

        {/* Frame */}
        <rect x={padLeft} y={padTop} width={chartW} height={chartH} fill="none" stroke={C.border} strokeWidth="1.5" />
      </svg>
    </div>
  );
}

// ============================================================================
// 4. Bar Chart: Fact Checks by Category
// ============================================================================
export function CategoryBarChart({ data = [] }) {
  const [hovered, setHovered] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-xs font-mono-tech text-[#111111]/50 border-2 border-dashed border-[#111111]/30">
        NO CATEGORY DATA
      </div>
    );
  }

  const maxVal = Math.max(1, ...data.map((d) => d.count || 0));

  return (
    <div className="space-y-2.5">
      {data.map((item, idx) => {
        const pct = Math.round(((item.count || 0) / maxVal) * 100);
        const isHov = hovered === idx;
        return (
          <div
            key={idx}
            className="cursor-default"
            onMouseEnter={() => setHovered(idx)}
            onMouseLeave={() => setHovered(null)}
          >
            <div className="mb-1 flex items-center justify-between text-xs font-mono-tech font-bold uppercase">
              <span className="text-[#111111]">{item.category}</span>
              <span className={`px-1.5 py-0.5 border border-[#111111] text-[10px] ${isHov ? "bg-[#B7FF3C]" : "bg-[#F5F1E8]"}`}>
                {item.count} checks
              </span>
            </div>
            <div className="h-3 w-full border border-[#111111] bg-[#F5F1E8] overflow-hidden">
              <div
                className="h-full transition-all duration-300"
                style={{ width: `${pct}%`, backgroundColor: isHov ? C.accent : C.border }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// 5. Multi-Bar Chart: Daily AI Invocations
// ============================================================================
export function DailyAiVolumeChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center font-mono-tech text-xs text-[#111111]/50 border-2 border-dashed border-[#111111]/30">
        NO TELEMETRY RECORDED
      </div>
    );
  }

  const maxCount = Math.max(1, ...data.map((d) => Math.max(d.bedrock || 0, d.textract || 0, d.tavily || 0)));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end gap-3 font-mono-tech text-[10px] font-bold uppercase text-[#111111]">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 border border-[#111111]" style={{ backgroundColor: C.blue }} /> Bedrock
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 border border-[#111111]" style={{ backgroundColor: C.amber }} /> Textract
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 border border-[#111111]" style={{ backgroundColor: C.purple }} /> Tavily
        </span>
      </div>

      <div className="flex h-36 items-end gap-1.5 border-b-2 border-l-2 border-[#111111] pb-1 pl-1">
        {data.map((item, idx) => {
          const bH = ((item.bedrock || 0) / maxCount) * 100;
          const tH = ((item.textract || 0) / maxCount) * 100;
          const tvH = ((item.tavily || 0) / maxCount) * 100;
          return (
            <div key={idx} className="flex flex-1 flex-col items-center gap-0.5">
              <div className="flex h-28 w-full items-end justify-center gap-0.5">
                <div style={{ height: `${bH}%`, backgroundColor: C.blue }} className="w-1/3 border border-[#111111] transition-all hover:opacity-80" title={`Bedrock: ${item.bedrock}`} />
                <div style={{ height: `${tH}%`, backgroundColor: C.amber }} className="w-1/3 border border-[#111111] transition-all hover:opacity-80" title={`Textract: ${item.textract}`} />
                <div style={{ height: `${tvH}%`, backgroundColor: C.purple }} className="w-1/3 border border-[#111111] transition-all hover:opacity-80" title={`Tavily: ${item.tavily}`} />
              </div>
              <span className="font-mono-tech text-[9px] text-[#111111]/60">{item.date?.slice(5)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
