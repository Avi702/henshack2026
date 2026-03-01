"use client";

import type { AppTab } from "@/types/api";

export default function HomePage({ onNavigate }: { onNavigate: (tab: AppTab) => void }) {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl mb-4">
          Unleash Your <span className="gradient-text">Potential</span>
        </h1>
        <p className="mx-auto max-w-lg text-lg text-zinc-400">
          Perfect your form, lift heavier, and avoid injuries with AI-driven real-time analysis for Squats, Bench, and Deadlifts.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <button
            onClick={() => onNavigate("analyze")}
            className="rounded-full bg-accent px-8 py-4 text-base font-bold text-white shadow-lg shadow-accent/20 transition-all hover:bg-orange-500 hover:scale-105 hover:shadow-accent/40"
          >
            Start Analyzing
          </button>
          <button
            onClick={() => onNavigate("learn")}
            className="rounded-full border border-zinc-700 bg-zinc-800/50 px-8 py-4 text-base font-bold text-white transition-all hover:bg-zinc-700 hover:scale-105"
          >
            Learn Form
          </button>
        </div>
      </section>

      {/* Features Grid */}
      <section className="grid gap-6 sm:grid-cols-2">
        <div className="rounded-3xl border border-card-border bg-card p-6 transition-all hover:border-zinc-600 hover:bg-zinc-800/80">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-bold">Smart Analysis</h2>
          <p className="text-sm text-zinc-400">
            Upload your videos or record straight from your device. Our AI detects joints, calculates angles, and identifies errors like butt wink, rounding backs, or uneven bar paths.
          </p>
        </div>
        
        <div className="rounded-3xl border border-card-border bg-card p-6 transition-all hover:border-zinc-600 hover:bg-zinc-800/80">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-green-500/10 text-green-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-bold">Track Progress</h2>
          <p className="text-sm text-zinc-400">
            Keep a log of your working sets, reps, and weights. Monitor your volume and intensity over time with integrated tracking charts.
          </p>
        </div>
      </section>

      {/* Testimonials */}
      <section className="rounded-3xl border border-card-border bg-gradient-to-b from-zinc-800/40 to-transparent p-8 text-center">
        <blockquote className="mx-auto max-w-xl text-lg italic text-zinc-300">
          "This app completely transformed my squat! Being able to see exactly where my depth was off has helped me add 50lbs to my PR without any knee pain."
        </blockquote>
        <p className="mt-4 text-sm font-bold text-accent">— Alex P, Powerlifter</p>
      </section>
    </div>
  );
}
