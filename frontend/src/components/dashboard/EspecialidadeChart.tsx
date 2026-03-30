"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { EspecialidadeDataPoint } from "@/lib/types";

export function EspecialidadeChart({ data }: { data: EspecialidadeDataPoint[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Consultas por Especialidade</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8ece9" />
          <XAxis dataKey="especialidade" tick={{ fill: "#5a6b5f", fontSize: 11 }} />
          <YAxis tick={{ fill: "#5a6b5f", fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="count" name="Consultas" fill="#2e9e60" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
