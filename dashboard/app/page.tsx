"use client";
import { useEffect, useState } from "react";
import { getDailyProduction, getMonthlySummary, getTopParties } from "../services/api";
import DailyLineChart from "../components/LineChart";
import PartyBarChart from "../components/BarChart";
import PartyPieChart from "../components/PieChart";
import PartyTable from "../components/PartyTable";

export default function Home() {
  const [daily, setDaily] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [topParties, setTopParties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([getDailyProduction(), getMonthlySummary(), getTopParties()])
      .then(([dailyRes, monthlyRes, partiesRes]) => {
        setDaily(dailyRes.data);
        setMonthly(monthlyRes.data);
        setTopParties(partiesRes.data);
      })
      .catch((err) => {
        console.error("Failed to load dashboard data:", err);
        setError("Failed to load dashboard data. Is the backend running?");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-zinc-950">
        <p className="text-lg text-zinc-500">Loading dashboard…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-zinc-50 dark:bg-zinc-950">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 max-w-md text-center">
          <p className="text-red-700 font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 md:p-10 space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          Production Dashboard
        </h1>
        <p className="text-zinc-500 mt-1">Overview of daily production, monthly invoices & top parties</p>
      </header>

      {/* Daily Production */}
      <section className="rounded-xl bg-white dark:bg-zinc-900 shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-zinc-800 dark:text-zinc-100">Daily Production</h2>
        {daily.length > 0 ? <DailyLineChart data={daily} /> : <p className="text-zinc-400">No data available.</p>}
      </section>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="rounded-xl bg-white dark:bg-zinc-900 shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-zinc-800 dark:text-zinc-100">Top Parties by Revenue</h2>
          {topParties.length > 0 ? <PartyBarChart data={topParties} /> : <p className="text-zinc-400">No data available.</p>}
        </section>
        <section className="rounded-xl bg-white dark:bg-zinc-900 shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-zinc-800 dark:text-zinc-100">Revenue Share (%)</h2>
          {topParties.length > 0 ? <PartyPieChart data={topParties} /> : <p className="text-zinc-400">No data available.</p>}
        </section>
      </div>

      {/* Table */}
      <section className="rounded-xl bg-white dark:bg-zinc-900 shadow p-6">
        <h2 className="text-lg font-semibold mb-4 text-zinc-800 dark:text-zinc-100">Party Summary</h2>
        {topParties.length > 0 ? <PartyTable data={topParties} /> : <p className="text-zinc-400">No data available.</p>}
      </section>
    </div>
  );
}
