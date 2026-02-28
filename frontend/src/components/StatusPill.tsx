"use client";

import type { AppStatus } from "@/types/api";

const CONFIG: Record<
  AppStatus,
  { label: string; color: string; animate?: boolean }
> = {
  idle: { label: "Ready", color: "bg-slate-700 text-slate-300" },
  uploading: {
    label: "Uploading…",
    color: "bg-blue-900/60 text-blue-300",
    animate: true,
  },
  analyzing: {
    label: "Analyzing…",
    color: "bg-indigo-900/60 text-indigo-300",
    animate: true,
  },
  done: { label: "Complete", color: "bg-green-900/60 text-green-300" },
  error: { label: "Error", color: "bg-red-900/60 text-red-300" },
};

export default function StatusPill({ status }: { status: AppStatus }) {
  const c = CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${c.color}`}
    >
      {c.animate && (
        <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
      )}
      {c.label}
    </span>
  );
}
