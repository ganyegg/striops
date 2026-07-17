"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import { formatZAR, type ScenarioOption } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function shortName(fn: string): string {
  return fn
    .replace("Water and Sanitation", "Water")
    .replace("Roads and Transport", "Roads")
    .replace("Solid Waste Management", "Waste")
    .replace("Community and Libraries", "Libraries");
}

export default function BudgetSpendChart({
  scenarios,
  compact = false,
}: {
  scenarios: ScenarioOption[];
  compact?: boolean;
}) {
  const rows = [...scenarios]
    .filter((s) => s.current_budget > 0)
    .sort((a, b) => b.current_budget - a.current_budget)
    .slice(0, 5);

  const labels = rows.map((r) => shortName(r.function_name));
  const spent = rows.map((r) => r.current_actual);
  const unspent = rows.map((r) => Math.max(0, r.current_budget - r.current_actual));
  const totalBudget = rows.reduce((a, r) => a + r.current_budget, 0);
  const totalUnspent = rows.reduce((a, r) => a + Math.max(0, r.current_budget - r.current_actual), 0);

  const option: EChartsOption = {
    backgroundColor: "transparent",
    grid: { left: 88, right: 16, top: 28, bottom: 8 },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "#0e181c",
      borderColor: "#1f2d32",
      textStyle: { color: "#e7edee", fontSize: 12 },
      valueFormatter: (v) => formatZAR(Number(v)),
    },
    legend: {
      data: ["Spent", "Unspent"],
      textStyle: { color: "#8ea3a8", fontSize: 11 },
      top: 0,
      right: 0,
      itemWidth: 10,
      itemHeight: 10,
    },
    xAxis: {
      type: "value",
      axisLabel: {
        color: "#5c6f74",
        fontSize: 10,
        formatter: (v: number) => formatZAR(v),
      },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
      axisLine: { show: false },
    },
    yAxis: {
      type: "category",
      data: labels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#b8c9ce", fontSize: 11 },
    },
    series: [
      {
        name: "Spent",
        type: "bar",
        stack: "total",
        barWidth: compact ? 12 : 16,
        itemStyle: { color: "#14b8a6", borderRadius: [0, 0, 0, 0] },
        data: spent,
      },
      {
        name: "Unspent",
        type: "bar",
        stack: "total",
        barWidth: compact ? 12 : 16,
        itemStyle: { color: "#f59e0b", borderRadius: [0, 4, 4, 0] },
        data: unspent,
      },
    ],
  };

  return (
    <div className="card overflow-hidden p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-helm-accent/80">Fiscal pulse</p>
          <h3 className="mt-1 font-display text-base font-semibold text-white">Budget vs unspent</h3>
        </div>
        <div className="text-right">
          <p className="font-display text-lg font-semibold tabular-nums text-helm-sand">
            {formatZAR(totalUnspent)}
          </p>
          <p className="text-[10px] uppercase tracking-wide text-white/40">
            idle of {formatZAR(totalBudget)}
          </p>
        </div>
      </div>
      <div className={compact ? "mt-1 h-52 w-full" : "mt-1 h-64 w-full"}>
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
      <p className="mt-1 text-[11px] leading-snug text-white/40">
        Latest seed year per function — amber is the redeployable gap the simulator can stress-test.
      </p>
    </div>
  );
}
