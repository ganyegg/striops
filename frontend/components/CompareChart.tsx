"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { ComparativeSeries } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const COLORS = ["#14b8a6", "#38bdf8", "#f59e0b", "#f87171"];

export default function CompareChart({ series }: { series: ComparativeSeries[] }) {
  const categories = Array.from(
    new Set(series.flatMap((s) => s.points.map((p) => p.period.slice(0, 7)))),
  ).sort();

  const dualAxis = series.length === 2 && series[0].unit !== series[1].unit;

  const option: EChartsOption = {
    backgroundColor: "transparent",
    grid: { left: 48, right: dualAxis ? 48 : 24, top: 40, bottom: 36 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0e181c",
      borderColor: "#1f2d32",
      textStyle: { color: "#e7edee", fontSize: 12 },
    },
    legend: {
      data: series.map((s) => s.label),
      textStyle: { color: "#8ea3a8", fontSize: 11 },
      top: 0,
    },
    xAxis: {
      type: "category",
      data: categories,
      axisLine: { lineStyle: { color: "#1f2d32" } },
      axisLabel: { color: "#5c6f74", fontSize: 10 },
    },
    yAxis: dualAxis
      ? [
          {
            type: "value",
            name: series[0].unit || "",
            nameTextStyle: { color: "#5c6f74", fontSize: 10 },
            splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
            axisLabel: { color: "#5c6f74" },
          },
          {
            type: "value",
            name: series[1].unit || "",
            nameTextStyle: { color: "#5c6f74", fontSize: 10 },
            splitLine: { show: false },
            axisLabel: { color: "#5c6f74" },
          },
        ]
      : {
          type: "value",
          name: series[0]?.unit || "",
          nameTextStyle: { color: "#5c6f74", fontSize: 10 },
          splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
          axisLabel: { color: "#5c6f74" },
        },
    series: series.map((s, i) => ({
      name: s.label,
      type: "line",
      smooth: true,
      yAxisIndex: dualAxis ? i : 0,
      showSymbol: true,
      symbolSize: 6,
      lineStyle: { width: 2.5, color: COLORS[i % COLORS.length] },
      itemStyle: { color: COLORS[i % COLORS.length] },
      data: categories.map((c) => {
        const hit = s.points.find((p) => p.period.slice(0, 7) === c);
        return hit ? hit.value : null;
      }),
    })),
  };

  return (
    <div className="h-64 w-full">
      <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
    </div>
  );
}
