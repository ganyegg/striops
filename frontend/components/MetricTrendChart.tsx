"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { ChartPoint } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export default function MetricTrendChart({
  series,
  projected,
  unit,
  label,
}: {
  series: ChartPoint[];
  projected?: ChartPoint[];
  unit?: string | null;
  label: string;
}) {
  const categories = [
    ...series.map((p) => p.period.slice(0, 7)),
    ...(projected || [])
      .filter((p) => p.period !== series[series.length - 1]?.period)
      .map((p) => p.period.slice(0, 7)),
  ];

  // Align projected series to full category axis (nulls before projection).
  const actualData = categories.map((c) => {
    const hit = series.find((p) => p.period.slice(0, 7) === c);
    return hit ? hit.value : null;
  });
  const projectedData = categories.map((c) => {
    const hit = (projected || []).find((p) => p.period.slice(0, 7) === c);
    return hit ? hit.value : null;
  });

  const option: EChartsOption = {
    backgroundColor: "transparent",
    grid: { left: 48, right: 24, top: 36, bottom: 40 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0e181c",
      borderColor: "#1f2d32",
      textStyle: { color: "#e7edee", fontSize: 12 },
    },
    legend: {
      data: ["Actual", "Projected"],
      textStyle: { color: "#8ea3a8", fontSize: 11 },
      top: 0,
    },
    xAxis: {
      type: "category",
      data: categories,
      axisLine: { lineStyle: { color: "#1f2d32" } },
      axisLabel: { color: "#5c6f74", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: unit || "",
      nameTextStyle: { color: "#5c6f74", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1a262b" } },
      axisLabel: { color: "#5c6f74", fontSize: 10 },
    },
    series: [
      {
        name: "Actual",
        type: "line",
        data: actualData,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: "#5b8cff", width: 2.5 },
        itemStyle: { color: "#5b8cff" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(91,140,255,0.25)" },
              { offset: 1, color: "rgba(91,140,255,0)" },
            ],
          },
        },
      },
      {
        name: "Projected",
        type: "line",
        data: projectedData,
        smooth: true,
        symbol: "diamond",
        symbolSize: 6,
        lineStyle: { color: "#e8c37a", width: 2, type: "dashed" },
        itemStyle: { color: "#e8c37a" },
        connectNulls: false,
      },
    ],
  };

  return (
    <div className="card p-4">
      <p className="mb-1 text-xs uppercase tracking-[0.2em] text-white/40">Trend · {label}</p>
      <div className="h-72 w-full">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </div>
    </div>
  );
}
