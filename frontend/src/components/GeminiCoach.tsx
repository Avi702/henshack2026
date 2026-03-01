"use client";

import { useState, useEffect } from "react";
import type { AnalysisResult } from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function GeminiCoach({ result }: { result: AnalysisResult }) {
  const [coaching, setCoaching] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchCoaching() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE}/coaching`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            lift_type: result.lift_type,
            overall_label: result.overall.label,
            score: result.score,
            mse_mean: result.mse_mean,
            issues: result.issues,
            ai_feedback_summary: result.ai_feedback.summary,
            ai_feedback_bullets: result.ai_feedback.bullets,
          }),
        });
        if (!res.ok) throw new Error(`Server ${res.status}`);
        const data = await res.json();
        if (!cancelled) setCoaching(data.coaching);
      } catch (err) {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Failed to load coaching"
          );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchCoaching();
    return () => {
      cancelled = true;
    };
  }, [result]);

  return (
    <div className="rounded-2xl border border-card-border bg-card p-6 animate-fade-in">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-amber-500">
          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold">AI Coach</h3>
          <p className="text-xs text-zinc-500">Powered by Gemini</p>
        </div>
      </div>

      {loading && (
        <div className="space-y-3">
          <div className="h-4 w-3/4 rounded bg-zinc-800 shimmer" />
          <div className="h-4 w-full rounded bg-zinc-800 shimmer" />
          <div className="h-4 w-5/6 rounded bg-zinc-800 shimmer" />
          <div className="h-4 w-2/3 rounded bg-zinc-800 shimmer" />
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {coaching && !loading && (
        <div className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
          {coaching}
        </div>
      )}
    </div>
  );
}
