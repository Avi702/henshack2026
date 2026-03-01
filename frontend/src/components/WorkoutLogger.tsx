"use client";

import { useState, useEffect, useCallback } from "react";
import type { WorkoutEntry, LiftType } from "@/types/api";
import ProgressChart from "./ProgressChart";

const STORAGE_KEY = "squatbuddy_workouts";
const LIFTS: { value: LiftType; label: string; emoji: string }[] = [
  { value: "squat", label: "Squat", emoji: "🏋️" },
  { value: "bench", label: "Bench", emoji: "💪" },
  { value: "deadlift", label: "Deadlift", emoji: "🔥" },
];

function loadWorkouts(): WorkoutEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveWorkouts(entries: WorkoutEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export default function WorkoutLogger() {
  const [entries, setEntries] = useState<WorkoutEntry[]>([]);
  const [liftType, setLiftType] = useState<LiftType>("squat");
  const [weight, setWeight] = useState("");
  const [reps, setReps] = useState("");
  const [unit, setUnit] = useState<"lbs" | "kg">("lbs");
  const [chartLift, setChartLift] = useState<LiftType>("squat");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setEntries(loadWorkouts());
    setMounted(true);
  }, []);

  const addEntry = useCallback(() => {
    const w = parseFloat(weight);
    const r = parseInt(reps, 10);
    if (isNaN(w) || w <= 0 || isNaN(r) || r <= 0) return;

    const entry: WorkoutEntry = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      date: new Date().toISOString().split("T")[0],
      liftType,
      weight: w,
      reps: r,
      unit,
    };

    const updated = [entry, ...entries];
    setEntries(updated);
    saveWorkouts(updated);
    setWeight("");
    setReps("");
  }, [weight, reps, liftType, unit, entries]);

  const removeEntry = useCallback(
    (id: string) => {
      const updated = entries.filter((e) => e.id !== id);
      setEntries(updated);
      saveWorkouts(updated);
    },
    [entries]
  );

  if (!mounted) return null;

  const recentEntries = entries.slice(0, 10);
  const chartEntries = entries
    .filter((e) => e.liftType === chartLift)
    .reverse();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Log workout form */}
      <div className="rounded-2xl border border-card-border bg-card p-6">
        <h3 className="mb-5 text-lg font-semibold">Log Workout</h3>

        {/* Lift type */}
        <div className="mb-4">
          <label className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-500">
            Exercise
          </label>
          <div className="flex gap-2">
            {LIFTS.map((l) => (
              <button
                key={l.value}
                onClick={() => setLiftType(l.value)}
                className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition-all ${
                  liftType === l.value
                    ? "bg-accent/15 text-accent ring-1 ring-accent/30"
                    : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                }`}
              >
                <span className="mr-1.5">{l.emoji}</span>
                {l.label}
              </button>
            ))}
          </div>
        </div>

        {/* Weight + Reps + Unit row */}
        <div className="mb-4 flex gap-3">
          <div className="flex-1">
            <label className="mb-1.5 block text-xs font-medium text-zinc-500">
              Weight
            </label>
            <input
              type="number"
              min="0"
              step="2.5"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="135"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/20"
            />
          </div>
          <div className="flex-1">
            <label className="mb-1.5 block text-xs font-medium text-zinc-500">
              Reps
            </label>
            <input
              type="number"
              min="1"
              value={reps}
              onChange={(e) => setReps(e.target.value)}
              placeholder="5"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/20"
            />
          </div>
          <div className="w-24">
            <label className="mb-1.5 block text-xs font-medium text-zinc-500">
              Unit
            </label>
            <div className="flex rounded-xl bg-zinc-800 p-0.5">
              {(["lbs", "kg"] as const).map((u) => (
                <button
                  key={u}
                  onClick={() => setUnit(u)}
                  className={`flex-1 rounded-lg py-3 text-xs font-semibold transition-colors ${
                    unit === u
                      ? "bg-zinc-600 text-white"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={addEntry}
          disabled={!weight || !reps}
          className="w-full rounded-xl bg-accent py-3.5 text-sm font-bold text-white transition-all hover:bg-orange-500 disabled:cursor-not-allowed disabled:opacity-30"
        >
          Log Set
        </button>
      </div>

      {/* Progress chart */}
      {entries.length > 0 && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold">Progress</h3>
            <div className="flex gap-1 rounded-xl bg-zinc-800 p-0.5">
              {LIFTS.map((l) => (
                <button
                  key={l.value}
                  onClick={() => setChartLift(l.value)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                    chartLift === l.value
                      ? "bg-zinc-600 text-white"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          {chartEntries.length > 0 ? (
            <ProgressChart entries={chartEntries} unit={unit} />
          ) : (
            <p className="py-8 text-center text-sm text-zinc-500">
              No {chartLift} entries yet. Log a set to see your progress.
            </p>
          )}
        </div>
      )}

      {/* Recent entries */}
      {recentEntries.length > 0 && (
        <div className="rounded-2xl border border-card-border bg-card p-6">
          <h3 className="mb-4 text-lg font-semibold">Recent Sets</h3>
          <div className="space-y-2">
            {recentEntries.map((entry) => {
              const lift = LIFTS.find((l) => l.value === entry.liftType);
              return (
                <div
                  key={entry.id}
                  className="group flex items-center justify-between rounded-xl bg-zinc-800/50 px-4 py-3 transition-colors hover:bg-zinc-800"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-base">{lift?.emoji}</span>
                    <div>
                      <p className="text-sm font-medium">
                        {entry.weight} {entry.unit} x {entry.reps}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {lift?.label} &middot; {entry.date}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeEntry(entry.id)}
                    className="text-zinc-600 opacity-0 transition-all hover:text-red-400 group-hover:opacity-100"
                    aria-label="Delete"
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
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
