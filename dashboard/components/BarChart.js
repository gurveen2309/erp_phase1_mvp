"use client";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export default function PartyBarChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <XAxis
          dataKey="party_name"
          tick={{ fontSize: 11 }}
          angle={-30}
          textAnchor="end"
          height={60}
        />
        <YAxis />
        <Tooltip />
        <Bar
          dataKey="total_amount"
          fill="#6366f1"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}