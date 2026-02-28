"use client";

import { useRef, useState, useEffect } from "react";
import type { AnalysisResult, LiftType, AppStatus, InputMode } from "@/types/api";
import Recorder, { type RecorderHandle } from "@/components/Recorder";
import Uploader, { type UploaderHandle } from "@/components/Uploader";
import StatusPill from "@/components/StatusPill";
import ResultCard from "@/components/ResultCard";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const LIFTS: { value: LiftType; label: string }[] = [
  { value: "squat", label: "Squat" },
  { value: "bench", label: "Bench" },
  { value: "deadlift", label: "Deadlift" },
];

const TIPS = [
  "Get your full body in frame from head to feet",
  "Film from a 45° angle for best pose detection",
  "Use good, even lighting — avoid backlighting",
  "Keep camera steady (tripod or propped up)",
];

export default function Home() {
  const recorderRef = useRef<RecorderHandle>(null);
  const uploaderRef = useRef<UploaderHandle>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const [mode, setMode] = useState<InputMode>("record");
  const [liftType, setLiftType] = useState<LiftType>("squat");
  const [status, setStatus] = useState<AppStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const [clipReady, setClipReady] = useState(false);

  // Auto-scroll to results
  useEffect(() => {
    if (status === "done" && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [status]);

  async function handleAnalyze() {
    const blob =
      mode === "record"
        ? recorderRef.current?.getBlob()
        : uploaderRef.current?.getBlob();

    if (!blob) return;

    setError(null);
    setResult(null);
    setStatus("uploading");

    const form = new FormData();
    const ext =
      mode === "upload" && blob instanceof File
        ? blob.name.split(".").pop() ?? "webm"
        : "webm";
    form.append("file", blob, `recording.${ext}`);
    form.append("lift_type", liftType);
    form.append("return_artifacts", "true");

    try {
      setStatus("analyzing");
      const res = await fetch(`${API_BASE}/analyze/video`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server ${res.status}: ${text.slice(0, 200)}`);
      }
      const data: AnalysisResult = await res.json();
      setResult(data);
      setStatus("done");
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Is the backend running?"
      );
      setStatus("error");
    }
  }

  function handleReset() {
    recorderRef.current?.reset();
    uploaderRef.current?.reset();
    setResult(null);
    setError(null);
    setStatus("idle");
    setClipReady(false);
  }

  const isProcessing = status === "uploading" || status === "analyzing";

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="px-5 pt-14 pb-10 text-center sm:pt-20 sm:pb-14">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
          Hen<span className="text-accent">Hacks</span>
        </h1>
        <p className="mx-auto mt-3 max-w-md text-base text-slate-400 sm:text-lg">
          AI-powered lift form analysis. Record or upload a video and get
          instant feedback on your technique.
        </p>
      </header>

      <main className="mx-auto max-w-xl space-y-6 px-4 pb-20">
        {/* Input card */}
        <section className="rounded-2xl border border-card-border bg-card p-5 sm:p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Input</h2>
            <StatusPill status={status} />
          </div>

          {/* Mode toggle */}
          <div className="mb-5 flex rounded-xl bg-slate-800 p-1">
            {(["record", "upload"] as InputMode[]).map((m) => (
              <button
                key={m}
                disabled={isProcessing}
                onClick={() => {
                  setMode(m);
                  setClipReady(false);
                }}
                className={`flex-1 rounded-lg py-2 text-sm font-semibold capitalize transition-colors ${
                  mode === m
                    ? "bg-accent text-white shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          {/* Lift selector */}
          <div className="mb-5">
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">
              Lift Type
            </label>
            <div className="flex gap-2">
              {LIFTS.map((l) => (
                <button
                  key={l.value}
                  disabled={isProcessing}
                  onClick={() => setLiftType(l.value)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    liftType === l.value
                      ? "bg-accent/20 text-accent ring-1 ring-accent/40"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input area */}
          {mode === "record" ? (
            <Recorder ref={recorderRef} onClipChange={setClipReady} />
          ) : (
            <Uploader ref={uploaderRef} onClipChange={setClipReady} />
          )}

          {/* Action buttons */}
          <div className="mt-5 flex gap-3">
            <button
              disabled={isProcessing || !clipReady}
              onClick={handleAnalyze}
              className="flex-1 rounded-xl bg-accent py-3.5 text-base font-bold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isProcessing ? (
                <span className="inline-flex items-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  {status === "uploading" ? "Uploading…" : "Analyzing…"}
                </span>
              ) : (
                "Analyze"
              )}
            </button>
            <button
              onClick={handleReset}
              disabled={isProcessing}
              className="rounded-xl border border-slate-700 px-5 py-3.5 text-sm font-medium text-slate-400 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Reset
            </button>
          </div>
        </section>

        {/* Tips */}
        <section className="rounded-2xl border border-card-border bg-card p-5 sm:p-6">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
            Camera Setup Tips
          </h3>
          <ul className="space-y-2">
            {TIPS.map((tip, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-slate-400"
              >
                <span className="mt-0.5 shrink-0 text-accent">&#10003;</span>
                {tip}
              </li>
            ))}
          </ul>
        </section>

        {/* Processing shimmer */}
        {isProcessing && (
          <div className="shimmer rounded-2xl border border-card-border bg-card p-10 text-center">
            <p className="text-sm text-slate-400">
              {status === "uploading"
                ? "Sending your video to the server…"
                : "Running pose estimation & form analysis…"}
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-2xl bg-red-900/30 p-5 text-sm text-red-300">
            <p className="font-semibold">Something went wrong</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {/* Results */}
        {status === "done" && result && (
          <div ref={resultsRef}>
            <h2 className="mb-4 text-xl font-bold">Results</h2>
            <ResultCard result={result} />
          </div>
        )}
      </main>
    </div>
  );
}
