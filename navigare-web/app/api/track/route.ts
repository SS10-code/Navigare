import { NextRequest, NextResponse } from "next/server";

interface TrackEvent {
  event: string;
  userId?: string;
  guestId?: string;
  properties?: Record<string, unknown>;
  timestamp?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: TrackEvent = await request.json();

    if (!body.event) {
      return NextResponse.json({ error: "Missing event field" }, { status: 400 });
    }

    const eventRecord = {
      ...body,
      timestamp: body.timestamp || new Date().toISOString(),
      userAgent: request.headers.get("user-agent"),
      ip: request.headers.get("x-forwarded-for") || "unknown",
    };

    // In production, forward to GA4/Mixpanel server-side or persist to database.
    // For now, log to server console for observability.
    console.log("[TRACK]", JSON.stringify(eventRecord));

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error("Track endpoint error:", error);
    return NextResponse.json({ error: "Failed to process event" }, { status: 500 });
  }
}
