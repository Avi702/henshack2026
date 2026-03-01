"use client";

import { useState } from "react";
import type { AnalysisResult } from "@/types/api";
import VideoPlayer from "./VideoPlayer";
import GeminiCoach from "./GeminiCoach";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const LABEL_STYLE: Record<string, { bg: string; text: string; icon: string }> = {
  good_form: {
    bg: "from-emerald-900/40 to-emerald-900/20 border-emerald-700/30",
    text: "text-emerald-300",
    icon: "✓",
  },
  bad_form: {
    bg: "from-red-900/40 to-red-900/20 border-red-700/30",
    text: "text-red-300",
    icon: "✗",
  },
  unknown: {
    bg: "from-zinc-800/40 to-zinc-800/20 border-zinc-700/30",
    text: "text-zinc-400",
    icon: "?",
  },
};

const SEVERITY_STYLE: Record<string, string> = {
  low: "bg-yellow-900/30 text-yellow-300 border border-yellow-800/30",
  medium: "bg-orange-900/30 text-orange-300 border border-orange-800/30",
  high: "bg-red-900/30 text-red-300 border border-red-800/30",
};

function artifactUrl(path: string | null): string | null {
  if (!path) return null;
  return `${API_BASE}${path}`;
}

export default function ResultCard({ result }: { result: AnalysisResult }) {
  const [showJson, setShowJson] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  const isUnknown = result.overall.label === "unknown";
  const style = LABEL_STYLE[result.overall.label] ?? LABEL_STYLE.unknown;

  return (
    <div className="space-y-5 animate-slide-up">
      {/* Overall verdict */}
      <div className={`rounded-2xl border bg-gradient-to-br ${style.bg} p-6`}>
        <div className="flex items-center gap-4">
          <div
            className={`flex h-14 w-14 items-center justify-center rounded-2xl text-2xl font-bold ${style.text} bg-black/20`}
          >
            {style.icon}
          </div>
          <div>
            <p className={`text-2xl font-bold capitalize ${style.text}`}>
              {result.overall.label.replace(/_/g, " ")}
            </p>
            {result.overall.confidence > 0 && (
              <p className="mt-0.5 text-sm text-zinc-400">
                {(result.overall.confidence * 100).toFixed(1)}% confidence
              </p>
            )}
          </div>
        </div>

        {isUnknown && (
          <p className="mt-4 rounded-xl bg-black/20 p-3 text-sm text-zinc-400">
            No expert model available for this lift type yet.
          </p>
        )}

        {(result.score != null || result.mse_mean != null) && (
          <div className="mt-5 flex gap-8">
            {result.score != null && (
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Score
                </p>
                <p className="mt-1 font-mono text-2xl font-bold">
                  {result.score.toFixed(2)}
                </p>
              </div>
            )}
            {result.mse_mean != null && (
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  MSE
                </p>
                <p className="mt-1 font-mono text-2xl font-bold">
                  {result.mse_mean.toFixed(5)}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Videos */}
      {(result.artifacts.annotated_video_url ||
        result.artifacts.comparison_video_url) && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-4 text-lg font-semibold">Form Analysis Video</h3>
          <div className="space-y-4">
            {result.artifacts.annotated_video_url && (
              <VideoPlayer
                src={artifactUrl(result.artifacts.annotated_video_url)!}
                label="Annotated Skeleton Overlay"
              />
            )}
            {result.artifacts.comparison_video_url && (
              <VideoPlayer
                src={artifactUrl(result.artifacts.comparison_video_url)!}
                label="Expert Comparison"
              />
            )}
          </div>
        </div>
      )}

      {/* AI Coaching (Gemini) */}
      <GeminiCoach result={result} />

      {/* Built-in feedback */}
      {result.ai_feedback && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-3 text-lg font-semibold">Model Feedback</h3>
          <p className="text-sm text-zinc-300">{result.ai_feedback.summary}</p>
          {result.ai_feedback.bullets.length > 0 && (
            <ul className="mt-3 space-y-1.5 text-sm text-zinc-400">
              {result.ai_feedback.bullets.map((b, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                  {b}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Issues */}
      {result.issues.length > 0 && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-4 text-lg font-semibold">
            Detected Issues
            <span className="ml-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-900/40 text-xs font-bold text-red-300">
              {result.issues.length}
            </span>
          </h3>
          <div className="space-y-2.5">
            {result.issues.map((issue, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-xl bg-zinc-800/40 p-4"
              >
                <span
                  className={`mt-0.5 shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase ${
                    SEVERITY_STYLE[issue.severity] ?? ""
                  }`}
                >
                  {issue.severity}
                </span>
                <div className="min-w-0">
                  <p className="text-sm text-zinc-200">{issue.message}</p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {issue.code} &middot; frame {issue.evidence_frame}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Debug + Raw JSON */}
      <div className="flex gap-4 text-xs">
        <button
          onClick={() => setShowDebug(!showDebug)}
          className="text-zinc-600 transition-colors hover:text-zinc-400"
        >
          {showDebug ? "▾" : "▸"} Details
        </button>
        <button
          onClick={() => setShowJson(!showJson)}
          className="text-zinc-600 transition-colors hover:text-zinc-400"
        >
          {showJson ? "▾" : "▸"} Raw JSON
        </button>
      </div>

      {showDebug && (
        <p className="rounded-xl bg-zinc-900 p-3 text-xs text-zinc-500 animate-fade-in">
          Frames: {result.debug.frames_analyzed} &middot; Poses:{" "}
          {result.debug.poses_found}
          {result.debug.notes && <> &middot; {result.debug.notes}</>}
        </p>
      )}

      {showJson && (
        <pre className="max-h-60 overflow-auto rounded-xl bg-zinc-900 p-4 font-mono text-xs text-zinc-500 animate-fade-in">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
