export interface Issue {
  code: string;
  severity: "low" | "medium" | "high";
  message: string;
  evidence_frame: number;
}

export interface AnalysisResult {
  lift_type: string;
  overall: { label: "good_form" | "bad_form" | "unknown"; confidence: number };
  score: number | null;
  mse_mean: number | null;
  issues: Issue[];
  artifacts: {
    annotated_video_url: string | null;
    comparison_video_url: string | null;
  };
  ai_feedback: { summary: string; bullets: string[] };
  debug: { frames_analyzed: number; poses_found: number; notes: string };
}

export type LiftType = "squat" | "bench" | "deadlift";

export type AppStatus =
  | "idle"
  | "uploading"
  | "analyzing"
  | "done"
  | "error";

export type InputMode = "record" | "upload";

export type AppTab = "analyze" | "progress";

export interface WorkoutEntry {
  id: string;
  date: string;
  liftType: LiftType;
  weight: number;
  reps: number;
  unit: "lbs" | "kg";
}
