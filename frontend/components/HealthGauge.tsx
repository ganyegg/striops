"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

// echarts-for-react touches `window`, so load it client-only.
const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function colorFor(score: number): string {
  if (score >= 75) return "#4ade80";
  if (score >= 50) return "#fbbf24";
  return "#f87171";
}

export default function HealthGauge({ score }: { score: number }) {
  const color = colorFor(score);
  const option: EChartsOption = {
    series: [
      {
        type: "gauge",
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: "100%",
        progress: { show: true, width: 14, roundCap: true, itemStyle: { color } },
        axisLine: { lineStyle: { width: 14, color: [[1, "rgba(255,255,255,0.08)"]] } },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        anchor: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, 0],
          fontSize: 48,
          fontWeight: 700,
          color: "#f8fafc",
          formatter: "{value}",
        },
        data: [{ value: score }],
      },
    ],
  };

  return (
    <div className="relative h-56 w-full">
      <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      <div className="pointer-events-none absolute inset-x-0 bottom-6 text-center text-xs uppercase tracking-[0.2em] text-white/40">
        Strategic Health
      </div>
    </div>
  );
}
