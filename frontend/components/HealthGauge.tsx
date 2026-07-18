"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

// echarts-for-react touches `window`, so load it client-only.
const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function colorFor(score: number): string {
  if (score >= 75) return "#34d399";
  if (score >= 50) return "#fbbf24";
  return "#f87171";
}

export default function HealthGauge({
  score,
  compact = false,
}: {
  score: number;
  compact?: boolean;
}) {
  const color = colorFor(score);
  const option: EChartsOption = {
    series: [
      {
        type: "gauge",
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: compact ? "95%" : "100%",
        center: compact ? ["50%", "55%"] : ["50%", "50%"],
        progress: { show: true, width: compact ? 12 : 14, roundCap: true, itemStyle: { color } },
        axisLine: {
          lineStyle: { width: compact ? 12 : 14, color: [[1, "rgba(255,255,255,0.08)"]] },
        },
        pointer: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        anchor: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, "5%"],
          fontSize: compact ? 42 : 48,
          fontWeight: 700,
          color: "#f8fafc",
          formatter: "{value}",
          fontFamily: "Fraunces, Georgia, serif",
        },
        data: [{ value: score }],
      },
    ],
  };

  return (
    <div className={`relative w-full ${compact ? "h-44" : "h-56"}`}>
      <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      {!compact ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-6 text-center text-xs uppercase tracking-[0.2em] text-striops-sand/70">
          Strategic Health
        </div>
      ) : null}
    </div>
  );
}
