import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.RAILWAY_API_URL || process.env.NEXT_PUBLIC_RAILWAY_API_URL || "http://localhost:8000";
const API_TOKEN = process.env.API_TOKEN || "";

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/");
  const contentType = request.headers.get("content-type") || "";

  let body: BodyInit;
  const headers: Record<string, string> = {};

  if (contentType.includes("multipart/form-data")) {
    body = await request.formData();
  } else {
    body = await request.text();
    headers["Content-Type"] = "application/json";
  }

  if (API_TOKEN) {
    headers["Authorization"] = `Bearer ${API_TOKEN}`;
  }

  const res = await fetch(`${API_URL}/api/${path}`, {
    method: "POST",
    headers,
    body,
  });

  const data = await res.text();
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
  });
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join("/");
  const headers: Record<string, string> = {};
  if (API_TOKEN) {
    headers["Authorization"] = `Bearer ${API_TOKEN}`;
  }

  const res = await fetch(`${API_URL}/api/${path}`, {
    method: "GET",
    headers,
  });

  const data = await res.text();
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
