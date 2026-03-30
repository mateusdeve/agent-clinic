"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { TrendDataPoint } from "@/lib/types";

export function TrendChart({ data }: { data: TrendDataPoint[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Tendencia Semanal</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8ece9" />
          <XAxis dataKey="date" tick={{ fill: "#5a6b5f", fontSize: 12 }} />
          <YAxis tick={{ fill: "#5a6b5f", fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="consultas"
            name="Consultas"
            stroke="#2e9e60"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="no_shows"
            name="No-shows"
            stroke="#9aaa9e"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
