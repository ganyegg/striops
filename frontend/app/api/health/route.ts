import { NextResponse } from "next/server";

/** Lightweight liveness for Render — must not SSR the homepage or call the API. */
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  return NextResponse.json(
    { status: "ok", service: "striops-web" },
    { status: 200, headers: { "Cache-Control": "no-store" } },
  );
}
