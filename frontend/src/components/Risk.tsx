import { AlertOctagon, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { Level } from "../api";

// risk colours are always paired with an icon and a text label
export const LEVEL_STYLE: Record<Level, { text: string; bg: string; border: string; bar: string; icon: typeof Info }> = {
  High: {
    text: "text-red-700 dark:text-red-300",
    bg: "bg-red-50 dark:bg-red-950/40",
    border: "border-red-500",
    bar: "#dc2626",
    icon: AlertOctagon,
  },
  Medium: {
    text: "text-amber-700 dark:text-amber-300",
    bg: "bg-amber-50 dark:bg-amber-950/40",
    border: "border-amber-500",
    bar: "#d97706",
    icon: AlertTriangle,
  },
  Low: {
    text: "text-yellow-700 dark:text-yellow-300",
    bg: "bg-yellow-50 dark:bg-yellow-950/30",
    border: "border-yellow-400",
    bar: "#ca8a04",
    icon: Info,
  },
  Safe: {
    text: "text-green-700 dark:text-green-300",
    bg: "bg-green-50 dark:bg-green-950/30",
    border: "border-green-500",
    bar: "#16a34a",
    icon: CheckCircle2,
  },
};

export function RiskBadge({ level, small }: { level: Level; small?: boolean }) {
  const s = LEVEL_STYLE[level];
  const Icon = s.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${s.bg} ${s.text} ${
        small ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm"
      }`}
    >
      <Icon className={small ? "h-3.5 w-3.5" : "h-4 w-4"} aria-hidden />
      {level === "Safe" ? "Safe" : `${level} risk`}
    </span>
  );
}

export function scoreLevel(score: number): Level {
  if (score >= 70) return "High";
  if (score >= 40) return "Medium";
  if (score >= 15) return "Low";
  return "Safe";
}

export function Gauge({ score, size = 220 }: { score: number; size?: number }) {
  const level = scoreLevel(score);
  const r = 80;
  const c = Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  return (
    <svg viewBox="0 0 200 120" width={size} height={(size * 120) / 200} role="img" aria-label={`Risk score ${score} out of 100`}>
      <path d="M20 100 A80 80 0 0 1 180 100" fill="none" className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="16" strokeLinecap="round" />
      <path
        d="M20 100 A80 80 0 0 1 180 100"
        fill="none"
        stroke={LEVEL_STYLE[level].bar}
        strokeWidth="16"
        strokeLinecap="round"
        strokeDasharray={`${c * pct} ${c}`}
        style={{ transition: "stroke-dasharray 0.8s ease-out" }}
      />
      <text x="100" y="88" textAnchor="middle" className="fill-slate-900 dark:fill-white" fontSize="40" fontWeight="700">
        {score}
      </text>
      <text x="100" y="110" textAnchor="middle" className="fill-slate-500" fontSize="11">
        out of 100
      </text>
    </svg>
  );
}

export function ConfidenceBar({ value, color = "#4f46e5" }: { value: number; color?: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div className="h-full rounded-full" style={{ width: `${Math.round(value * 100)}%`, background: color }} />
      </div>
      <span className="w-10 text-right text-xs tabular-nums text-slate-500">{Math.round(value * 100)}%</span>
    </div>
  );
}
