"use client";

import type { AppStatus } from "@/types/api";

const CONFIG: Record<
  AppStatus,
  { label: string; color: string; animate?: boolean }
> = {
  idle: { label: "Ready", color: "bg-zinc-800 text-zinc-400" },
  uploading: {
    label: "Uploading",
    color: "bg-orange-900/40 text-orange-300",
    animate: true,
  },
  analyzing: {
    label: "Analyzing",
    color: "bg-amber-900/40 text-amber-300",
    animate: true,
  },
  done: { label: "Complete", color: "bg-emerald-900/40 text-emerald-300" },
  error: { label: "Error", color: "bg-red-900/40 text-red-300" },
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
