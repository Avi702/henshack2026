"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import type { WorkoutEntry } from "@/types/api";

interface Props {
  entries: WorkoutEntry[];
  unit: "lbs" | "kg";
}

export default function ProgressChart({ entries, unit }: Props) {
  const data = entries.map((e, i) => ({
    idx: i + 1,
    date: e.date,
    weight: e.weight,
    reps: e.reps,
    label: `${e.date}\n${e.weight}${e.unit} x${e.reps}`,
  }));

  if (data.length < 2) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        Log at least 2 sets to see your progress chart.
      </div>
    );
  }

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 8, right: 8, left: -12, bottom: 4 }}
        >
          <defs>
            <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#71717a", fontSize: 11 }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#71717a", fontSize: 11 }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
            unit={` ${unit}`}
          />
          <Tooltip
            contentStyle={{
              background: "#18181b",
              border: "1px solid #27272a",
              borderRadius: "12px",
              fontSize: "12px",
              color: "#fafafa",
            }}
            labelStyle={{ color: "#a1a1aa", marginBottom: 4 }}
            formatter={(value) => [`${value} ${unit}`, "Weight"]}
          />
          <Area
            type="monotone"
            dataKey="weight"
            stroke="#f97316"
            strokeWidth={2.5}
            fill="url(#weightGrad)"
            dot={{ fill: "#f97316", strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: "#fb923c", strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
