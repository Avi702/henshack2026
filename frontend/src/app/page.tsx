"use client";

import { useRef, useState, useEffect } from "react";
import type {
  AnalysisResult,
  LiftType,
  AppStatus,
  InputMode,
  AppTab,
} from "@/types/api";
import Recorder, { type RecorderHandle } from "@/components/Recorder";
import Uploader, { type UploaderHandle } from "@/components/Uploader";
import StatusPill from "@/components/StatusPill";
import ResultCard from "@/components/ResultCard";
import WorkoutLogger from "@/components/WorkoutLogger";
import HomePage from "@/components/HomePage";
import LearnPage from "@/components/LearnPage";
import ThemeToggle from "@/components/ThemeToggle";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const LIFTS: { value: LiftType; label: string }[] = [
  { value: "squat", label: "Squat" },
  { value: "bench", label: "Bench" },
  { value: "deadlift", label: "Deadlift" },
];

const TIPS = [
  "Get your full body in frame from head to feet",
  "Film from a 45 degree angle for best results",
  "Use good, even lighting — avoid backlighting",
  "Keep camera steady (tripod or propped up)",
];

export default function Home() {
  const recorderRef = useRef<RecorderHandle>(null);
  const uploaderRef = useRef<UploaderHandle>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const [tab, setTab] = useState<AppTab>("home");
  const [mode, setMode] = useState<InputMode>("record");
  const [liftType, setLiftType] = useState<LiftType>("squat");
  const [status, setStatus] = useState<AppStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [clipReady, setClipReady] = useState(false);

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
    <div className="min-h-screen relative overflow-hidden transition-colors duration-300">
      
      {/* Animated gradient blobs in background (moved behind content but ON TOP of body bg) */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden mix-blend-screen dark:mix-blend-screen opacity-70">
        <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] max-w-125 max-h-125 rounded-full bg-(--blob-1) blur-[80px] animate-blob" />
        <div className="absolute top-[20%] right-[-5%] w-[35vw] h-[35vw] max-w-112.5 max-h-112.5 rounded-full bg-(--blob-2) blur-[80px] animate-blob animation-delay-2000" />
        <div className="absolute bottom-[-10%] left-[20%] w-[45vw] h-[45vw] max-w-150 max-h-150 rounded-full bg-(--blob-3) blur-[80px] animate-blob animation-delay-4000" />
      </div>

      <div className="relative z-10 min-h-screen">
        {/* Header */}
        <header className="sticky top-0 z-50 border-b border-zinc-200 dark:border-zinc-800/50 bg-background/80 backdrop-blur-xl transition-colors">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-linear-to-br from-orange-500 to-amber-500 text-lg font-black text-white shadow-lg shadow-orange-500/20">
                S
              </div>
              <span className="text-lg font-bold tracking-tight">
                Squat<span className="gradient-text">Buddy</span>
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Tab navigation */}
              <nav className="flex rounded-xl bg-zinc-200 dark:bg-zinc-800/50 p-0.5 overflow-x-auto border border-zinc-300 dark:border-zinc-700/50">
                {(
                  [
                    { key: "home", label: "Home", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
                    { key: "learn", label: "Learn", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
                    { key: "analyze", label: "Analyze", icon: "M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" },
                    { key: "progress", label: "Progress", icon: "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" },
                  ] as const
                ).map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-all ${
                      tab === t.key
                        ? "bg-zinc-100 dark:bg-zinc-700 text-zinc-900 dark:text-white shadow"
                        : "text-zinc-600 dark:text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300"
                    }`}
                  >
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d={t.icon}
                      />
                    </svg>
                    {t.label}
                  </button>
                ))}
              </nav>
              <ThemeToggle />
            </div>
          </div>
        </header>

        <main className={`mx-auto ${tab === "learn" ? "max-w-6xl" : "max-w-3xl"} px-4 sm:px-6 lg:px-8 py-6 relative z-10 transition-all duration-500`}>
          
          {/* ═══ HOME TAB ═══ */}
          {tab === "home" && (
            <div className="animate-fade-in">
               <HomePage onNavigate={setTab} />
            </div>
          )}

          {/* ═══ LEARN TAB ═══ */}
          {tab === "learn" && (
            <div className="animate-fade-in">
               <LearnPage />
            </div>
          )}

          {/* ═══ ANALYZE TAB ═══ */}
          {tab === "analyze" && (
            <div className="space-y-6 animate-fade-in">
              {/* Hero */}
              <div className="text-center py-4">
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
                  AI Form <span className="gradient-text">Analysis</span>
                </h1>
                <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500">
                  Record or upload your lift and get instant AI-powered feedback on
                  your technique.
                </p>
              </div>

              {/* Input card */}
              <section className="rounded-2xl border border-card-border bg-card p-5 sm:p-6">
                <div className="mb-5 flex items-center justify-between">
                  <h2 className="text-base font-semibold">Input</h2>
                  <StatusPill status={status} />
                </div>

                {/* Mode toggle */}
                <div className="mb-5 flex rounded-xl bg-zinc-800/50 p-1">
                  {(["record", "upload"] as InputMode[]).map((m) => (
                    <button
                      key={m}
                      disabled={isProcessing}
                      onClick={() => {
                        setMode(m);
                        setClipReady(false);
                      }}
                      className={`flex-1 rounded-lg py-2.5 text-sm font-semibold capitalize transition-all ${
                        mode === m
                          ? "bg-accent text-white shadow-lg shadow-accent/20"
                          : "text-zinc-500 hover:text-zinc-300"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>

                {/* Lift selector */}
                <div className="mb-5">
                  <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Lift Type
                  </label>
                  <div className="flex gap-2">
                    {LIFTS.map((l) => (
                      <button
                        key={l.value}
                        disabled={isProcessing || l.value !== "squat"}
                        onClick={() => setLiftType(l.value)}
                        title={l.value !== "squat" ? "Expert model for this lift is still training!" : "Squat Expert Model Active"}
                        className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition-all ${
                          liftType === l.value
                            ? "bg-accent/15 text-accent ring-1 ring-accent/30"
                            : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 disabled:opacity-30 disabled:cursor-not-allowed"
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
                    className="flex-1 rounded-xl bg-accent py-3.5 text-sm font-bold text-white shadow-lg shadow-accent/20 transition-all hover:bg-orange-500 hover:shadow-accent/30 disabled:cursor-not-allowed disabled:opacity-30 disabled:shadow-none"
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
                        {status === "uploading" ? "Uploading..." : "Analyzing..."}
                      </span>
                    ) : (
                      "Analyze Form"
                    )}
                  </button>
                  <button
                    onClick={handleReset}
                    disabled={isProcessing}
                    className="rounded-xl border border-zinc-700 px-5 py-3.5 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    Reset
                  </button>
                </div>
              </section>

              {/* Tips */}
              <section className="rounded-2xl border border-card-border bg-card p-5 sm:p-6">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Tips for best results
                </h3>
                <ul className="space-y-2">
                  {TIPS.map((tip, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2.5 text-sm text-zinc-400"
                    >
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/10 text-xs text-accent">
                        {i + 1}
                      </span>
                      {tip}
                    </li>
                  ))}
                </ul>
              </section>

              {/* Processing shimmer */}
              {isProcessing && (
                <div className="shimmer rounded-2xl border border-card-border bg-card p-10 text-center">
                  <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-accent/10">
                    <svg
                      className="h-5 w-5 animate-spin text-accent"
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
                  </div>
                  <p className="text-sm text-zinc-500">
                    {status === "uploading"
                      ? "Sending your video to the server..."
                      : "Running pose estimation & form analysis..."}
                  </p>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="rounded-2xl bg-red-900/20 border border-red-800/30 p-5 text-sm text-red-300 animate-fade-in">
                  <p className="font-semibold">Something went wrong</p>
                  <p className="mt-1 text-red-400/80">{error}</p>
                </div>
              )}

              {/* Results */}
              {status === "done" && result && (
                <div ref={resultsRef}>
                  <h2 className="mb-5 text-xl font-bold">Results</h2>
                  <ResultCard result={result} />
                </div>
              )}
            </div>
          )}

          {/* ═══ PROGRESS TAB ═══ */}
          {tab === "progress" && (
            <div className="animate-fade-in">
              <div className="mb-6 text-center py-4">
                <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
                  Track Your <span className="gradient-text">Progress</span>
                </h1>
                <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500">
                  Log your sets and watch your strength grow over time.
                </p>
              </div>
              <WorkoutLogger />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="relative z-10 border-t border-zinc-200 dark:border-zinc-800/50 py-6 text-center text-xs text-zinc-500 dark:text-zinc-600 transition-colors">
          SquatBuddy &middot; Built at HenHacks 2026
        </footer>
      </div>
    </div>
  );
}
