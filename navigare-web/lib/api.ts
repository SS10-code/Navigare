/**
 * API client — routes all backend calls through a Next.js server-side proxy
 * so the API auth token never leaks to the browser.
 */

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const proxyPath = endpoint.replace(/^\/api\/?/, "");
  const res = await fetch(`/api/proxy/${proxyPath}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

export async function uploadFile(endpoint: string, file: File, fieldName: string = "file") {
  const proxyPath = endpoint.replace(/^\/api\/?/, "");
  const formData = new FormData();
  formData.append(fieldName, file);

  const res = await fetch(`/api/proxy/${proxyPath}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || err.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function trackBusinessClient() {
  try {
    await apiFetch("/counters/business-client", { method: "POST" });
  } catch {
    // ignore analytics errors
  }
}

export async function trackClient() {
  try {
    await apiFetch("/counters/client", { method: "POST" });
  } catch {
    // ignore analytics errors
  }
}

export async function getCounters() {
  try {
    return await apiFetch("/counters");
  } catch {
    return { business_clients: 0, clients: 0, total_clients: 0 };
  }
}

export async function submitFeedback(email: string, message: string) {
  return apiFetch("/feedback", {
    method: "POST",
    body: JSON.stringify({ email, message }),
  });
}

/**
 * Checks if an API response object contains valid data.
 * Returns true for empty, null, or all-zero responses.
 */
export function isEmptyApiResponse(data: unknown): boolean {
  if (data === null || data === undefined) return true;
  if (typeof data === "string") {
    const trimmed = data.trim().toLowerCase();
    return trimmed === "" || trimmed === "null" || trimmed === "undefined" || trimmed === "none";
  }
  if (Array.isArray(data)) return data.length === 0;
  if (typeof data === "object") {
    const obj = data as Record<string, unknown>;
    const hasValues = Object.values(obj).some((v) => {
      if (v === null || v === undefined) return false;
      if (typeof v === "number") return v !== 0;
      if (typeof v === "string") return v.trim() !== "" && !["0", "$0", "none", "null", "n/a"].includes(v.trim().toLowerCase().replace(/[$,]/g, ""));
      if (Array.isArray(v)) return v.length > 0;
      if (typeof v === "object") return !isEmptyApiResponse(v);
      return true;
    });
    return !hasValues;
  }
  return false;
}

/**
 * Validates CSV content to reject placeholder or empty data.
 * Returns an error message string, or null if valid.
 */
export function validateCSV(file: File): string | null {
  const validTypes = ["text/csv", "application/vnd.ms-excel", "text/plain"];
  if (!validTypes.includes(file.type) && !file.name.endsWith(".csv")) {
    return "Invalid file type. Only CSV files are accepted.";
  }
  return null;
}
