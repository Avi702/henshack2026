"use client";

import { useState } from "react";
import type { AnalysisResult } from "@/types/api";
import VideoPlayer from "./VideoPlayer";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const LABEL_STYLE: Record<string, string> = {
  good_form: "bg-green-900/50 text-green-300 border-green-700/50",
  bad_form: "bg-red-900/50 text-red-300 border-red-700/50",
  unknown: "bg-slate-700/50 text-slate-300 border-slate-600/50",
};

const SEVERITY_STYLE: Record<string, string> = {
  low: "bg-yellow-900/40 text-yellow-300",
  medium: "bg-orange-900/40 text-orange-300",
  high: "bg-red-900/40 text-red-300",
};

function artifactUrl(path: string | null): string | null {
  if (!path) return null;
  return `${API_BASE}${path}`;
}

export default function ResultCard({ result }: { result: AnalysisResult }) {
  const [showJson, setShowJson] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  const isUnknown = result.overall.label === "unknown";

  return (
    <div className="space-y-5">
      {/* Overall verdict */}
      <div className="rounded-2xl border border-card-border bg-card p-6">
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full border px-4 py-1.5 text-sm font-bold uppercase tracking-wide ${
              LABEL_STYLE[result.overall.label] ?? LABEL_STYLE.unknown
            }`}
          >
            {result.overall.label.replace(/_/g, " ")}
          </span>
          {result.overall.confidence > 0 && (
            <span className="text-sm text-slate-400">
              {(result.overall.confidence * 100).toFixed(1)}% confidence
            </span>
          )}
        </div>

        {isUnknown && (
          <p className="mt-3 rounded-lg bg-slate-800 p-3 text-sm text-slate-400">
            Model training is in progress for this lift type — pose overlay is
            still available in the annotated video below.
          </p>
        )}

        {(result.score != null || result.mse_mean != null) && (
          <div className="mt-4 flex gap-6 text-sm">
            {result.score != null && (
              <div>
                <span className="text-slate-500">Score</span>
                <p className="font-mono text-lg font-semibold">
                  {result.score.toFixed(4)}
                </p>
              </div>
            )}
            {result.mse_mean != null && (
              <div>
                <span className="text-slate-500">MSE Mean</span>
                <p className="font-mono text-lg font-semibold">
                  {result.mse_mean.toFixed(6)}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* AI Feedback */}
      {result.ai_feedback && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-2 text-lg font-semibold">AI Feedback</h3>
          <p className="text-slate-300">{result.ai_feedback.summary}</p>
          {result.ai_feedback.bullets.length > 0 && (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-400">
              {result.ai_feedback.bullets.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Issues */}
      {result.issues.length > 0 && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-3 text-lg font-semibold">Issues</h3>
          <div className="space-y-2">
            {result.issues.map((issue, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-xl bg-slate-800/60 p-3"
              >
                <span
                  className={`mt-0.5 shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold uppercase ${
                    SEVERITY_STYLE[issue.severity] ?? ""
                  }`}
                >
                  {issue.severity}
                </span>
                <div className="min-w-0">
                  <p className="text-sm text-slate-200">{issue.message}</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {issue.code} &middot; frame {issue.evidence_frame}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Videos */}
      {(result.artifacts.annotated_video_url ||
        result.artifacts.comparison_video_url) && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-3 text-lg font-semibold">Videos</h3>
          <div className="space-y-4">
            {result.artifacts.annotated_video_url && (
              <VideoPlayer
                src={artifactUrl(result.artifacts.annotated_video_url)!}
                label="Annotated"
              />
            )}
            {result.artifacts.comparison_video_url && (
              <VideoPlayer
                src={artifactUrl(result.artifacts.comparison_video_url)!}
                label="Comparison"
              />
            )}
          </div>
        </div>
      )}

      {/* Debug details */}
      <div>
        <button
          onClick={() => setShowDebug(!showDebug)}
          className="text-xs text-slate-500 hover:text-slate-300"
        >
          {showDebug ? "▾" : "▸"} Details
        </button>
        {showDebug && (
          <p className="mt-1 text-xs text-slate-500">
            Frames analyzed: {result.debug.frames_analyzed} &middot; Poses
            found: {result.debug.poses_found}
            {result.debug.notes && <> &middot; {result.debug.notes}</>}
          </p>
        )}
      </div>

      {/* Raw JSON */}
      <div>
        <button
          onClick={() => setShowJson(!showJson)}
          className="text-xs text-slate-500 hover:text-slate-300"
        >
          {showJson ? "▾" : "▸"} Raw JSON
        </button>
        {showJson && (
          <pre className="mt-2 max-h-80 overflow-auto rounded-xl bg-slate-900 p-4 font-mono text-xs text-slate-400">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
