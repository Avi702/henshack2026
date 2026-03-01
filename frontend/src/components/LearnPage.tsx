"use client";

import { useState } from "react";
import type { LiftType } from "@/types/api";
import AiCoach from "./AiCoach";

const LIFT_INFO: Record<LiftType, { title: string, desc: string, steps: string[], commonMistakes: string[], embedUrl: string }> = {
  squat: {
    title: "The Barbell Squat",
    desc: "The king of all exercises. It primarily targets the quadriceps, hamstrings, and glutes, while heavily taxing the core and lower back for stabilization.",
    embedUrl: "/3d/placeholder.html?type=squat",
    steps: [
      "Bar Placement: Rest the bar on your upper traps (high bar) or across your rear delts (low bar).",
      "Stance: Feet slightly wider than shoulder-width, toes pointed outwards at 15-30 degrees.",
      "Descent: Brace your core, hinge your hips backwards slightly, and bend your knees.",
      "Depth: Break parallel. The crease of the hip should drop below the top of the knee.",
      "Ascent: Drive out of the hole by pushing through your mid-foot and extending hips and knees simultaneously."
    ],
    commonMistakes: [
      "Butt Wink: Rounding of the lower back at the bottom of the squat",
      "Knee Valgus: Knees caving inwards during the ascent",
      "Good Morning Squat: Hips rising faster than the chest",
      "Inadequate Depth: Stopping above parallel"
    ]
  },
  bench: {
    title: "The Bench Press",
    desc: "The definitive upper body pressing movement. It builds the pectorals, anterior deltoids, and triceps.",
    embedUrl: "/3d/placeholder.html?type=bench",
    steps: [
      "Setup: Lie flat on the bench. Grip the bar slightly wider than shoulder-width.",
      "Arch: Retract your scapula (pinch shoulder blades together) and create a slight arch in your upper back. Plant feet firmly on the ground.",
      "Unrack: Unrack the bar and hold it directly over your shoulders with straight arms.",
      "Descent: Lower the bar in a controlled path to your lower chest/sternum, tucking your elbows to around a 45-degree angle.",
      "Ascent: Press the bar up and slightly back towards your face until your elbows are fully locked out."
    ],
    commonMistakes: [
      "Flared Elbows: T-posing which shifts load entirely to the shoulders and increases injury risk",
      "Bouncing: Dropping the bar onto the chest to use momentum",
      "Lifting Glutes: Hips coming off the bench to cheat the rep"
    ]
  },
  deadlift: {
    title: "The Deadlift",
    desc: "The ultimate test of raw strength. A full-body hinge movement heavily reliant on the posterior chain: hamstrings, glutes, and spinal erectors.",
    embedUrl: "/3d/placeholder.html?type=deadlift",
    steps: [
      "Stance: Stand with mid-foot directly under the bar. Stance should be relatively narrow (hip-width) for conventional.",
      "Grip: Bend over without dropping hips and grab the bar. Bring shins to the bar.",
      "Setup: Squeeze chest up to flatten your back. Engage lats by \"bending\" the bar around your shins. Hips should be higher than knees but lower than shoulders.",
      "The Pull: Leg press the weight off the floor. Keep the bar dragging against your shins and thighs.",
      "Lockout: Stand tall by driving hips forward and squeezing glutes. Do not over-extend your lower back."
    ],
    commonMistakes: [
      "Rounding Back: Flexion of the lumbar spine resembling a cat, risking disc injury",
      "Hips Shooting Up: Legs straightening before the bar leaves the floor (stiff-leg deadlift)",
      "Bar Drift: Bar traveling away from the body during the pull"
    ]
  }
};

export default function LearnPage() {
  const [activeLift, setActiveLift] = useState<LiftType>("squat");
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="space-y-6 animate-page-enter max-w-5xl mx-auto w-full relative pb-20">
      <div className="text-center py-4">
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Form <span className="gradient-text">Library</span>
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-zinc-500">
          Master the big three lifts with our comprehensive breakdown.
        </p>
      </div>

      <div className="flex flex-col gap-6 w-full transition-all duration-500">
        {/* Main Content: 3D Animation & Lift Information */}
        <div className="w-full space-y-6 min-w-0">
          {/* 3D Scene Viewer */}
          <div className="relative w-full h-64 sm:h-96 rounded-3xl overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900 shadow-inner transition-colors">
            <div className="absolute inset-0 z-0">
              <iframe 
                src={LIFT_INFO[activeLift].embedUrl} 
                title={LIFT_INFO[activeLift].title} 
                frameBorder="0" 
                className="w-full h-full"
              ></iframe>
            </div>
            
            <div className="absolute bottom-3 right-3 bg-zinc-900/60 backdrop-blur text-xs font-mono px-2 py-1 rounded text-zinc-300 z-20 pointer-events-none">Interactive 3D</div>
          </div>

          {/* Lift Selector Tabs */}
          <div className="flex gap-2 p-1 bg-zinc-200 dark:bg-zinc-800/50 border border-zinc-300 dark:border-transparent rounded-xl transition-colors">
            {(["squat", "bench", "deadlift"] as LiftType[]).map((lift) => (
              <button
                key={lift}
                onClick={() => setActiveLift(lift)}
                className={`flex-1 rounded-lg py-2.5 text-sm font-semibold capitalize transition-all z-10 ${
                  activeLift === lift
                    ? "bg-accent text-white shadow-lg"
                    : "text-zinc-600 dark:text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-300"
                }`}
              >
                {lift}
              </button>
            ))}
          </div>

          {/* Content Card */}
          <div className="rounded-3xl border border-card-border bg-card p-6 sm:p-8 shadow-xl shadow-black/50 overflow-hidden">
            <h2 className="text-2xl font-black mb-3">{LIFT_INFO[activeLift].title}</h2>
            <p className="text-zinc-600 dark:text-zinc-400 mb-8 leading-relaxed text-base sm:text-lg">
              {LIFT_INFO[activeLift].desc}
            </p>

            <div className="grid md:grid-cols-2 gap-8">
              <div className="h-full">
                <div className="flex items-center gap-2 mb-4">
                  <div className="p-1.5 bg-accent/20 text-accent rounded-lg">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-200 transition-colors">Execution Steps</h3>
                </div>
                
                <ul className="space-y-4">
                  {LIFT_INFO[activeLift].steps.map((step, idx) => {
                    const [title, desc] = step.split(": ");
                    return (
                      <li key={idx} className="flex gap-4">
                        <span className="shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-800 text-xs font-bold text-zinc-600 dark:text-zinc-400 border border-zinc-300 dark:border-zinc-700 transition-colors">
                          {idx + 1}
                        </span>
                        <div className="text-sm">
                          <span className="font-bold text-zinc-800 dark:text-zinc-200 transition-colors">{title}: </span>
                          <span className="text-zinc-600 dark:text-zinc-400 transition-colors">{desc}</span>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>

              <div className="bg-red-950/5 dark:bg-red-950/10 border border-red-900/10 dark:border-red-900/20 rounded-2xl p-5 h-full">
                <div className="flex items-center gap-2 mb-4">
                  <div className="p-1.5 bg-red-500/10 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded-lg">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-200 transition-colors">Common Mistakes</h3>
                </div>
                
                <ul className="space-y-3">
                  {LIFT_INFO[activeLift].commonMistakes.map((mistake, idx) => {
                    const [title, desc] = mistake.split(": ");
                    return (
                      <li key={idx} className="text-sm">
                        <span className="font-bold text-red-600 dark:text-red-300 transition-colors">{title}: </span>
                        <span className="text-red-500 dark:text-red-200/70 transition-colors">{desc}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Floating AI Chatbot Button & Panel */}
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
          {/* Chatbot Panel */}
          <div className={`overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] ${
            isChatOpen ? "h-[500px] w-[350px] sm:w-[400px] opacity-100 mb-4" : "h-0 w-0 opacity-0 pointer-events-none"
          }`}>
            <div className="h-full w-full rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl bg-card overflow-hidden">
              <AiCoach />
            </div>
          </div>

          {/* Floating Toggle Button */}
          <div className="flex items-center gap-3">
            {!isChatOpen && (
              <div className="bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 text-sm py-2 px-4 rounded-full shadow-lg border border-zinc-200 dark:border-zinc-700 animate-bounce origin-right hidden sm:block">
                Ask our AI Coach for help!
                <div className="absolute top-1/2 right-[-6px] -translate-y-1/2 w-3 h-3 bg-white dark:bg-zinc-800 border-r border-t border-zinc-200 dark:border-zinc-700 rotate-45"></div>
              </div>
            )}
            
            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              className="h-14 w-14 rounded-full bg-accent text-white shadow-xl shadow-accent/30 flex items-center justify-center transition-all hover:scale-110 active:scale-95"
            >
              {isChatOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
