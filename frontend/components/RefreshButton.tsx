"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { refreshHelm } from "@/lib/api";

export default function RefreshButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function onRefresh() {
    setBusy(true);
    setMsg(null);
    try {
      const result = await refreshHelm(true);
      setMsg(
        result.ok
          ? `Refreshed ${new Date(result.refreshed_at).toLocaleTimeString("en-ZA")}`
          : `Partial: ${result.ingestion_error || "check feeds"}`,
      );
      router.refresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={onRefresh}
        disabled={busy}
        className="rounded-full border border-helm-sky/40 bg-helm-sky/10 px-3 py-1.5 text-xs font-medium text-helm-sky transition hover:bg-helm-sky/20 disabled:opacity-50"
        title="Clear caches and re-pull public feeds so new data surfaces now"
      >
        {busy ? "Refreshing…" : "Refresh now"}
      </button>
      {msg ? <span className="max-w-[14rem] text-right text-[10px] text-white/40">{msg}</span> : null}
    </div>
  );
}
