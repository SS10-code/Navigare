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
