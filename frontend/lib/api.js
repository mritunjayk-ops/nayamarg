// Single place every backend call goes through. Adds a timeout and turns
// failures into a friendly { data, error } shape so the UI never hangs.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, { method = "GET", body, timeout = 120000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      let detail = `Something went wrong (${res.status}).`;
      try {
        const j = await res.json();
        if (j && j.detail) detail = typeof j.detail === "string" ? j.detail : detail;
      } catch {
        /* non-JSON error body */
      }
      return { data: null, error: detail };
    }
    return { data: await res.json(), error: null };
  } catch (err) {
    const error =
      err && err.name === "AbortError"
        ? "This is taking longer than expected. Please try again."
        : "Could not reach the server. Make sure the backend is running.";
    return { data: null, error };
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  base: API_BASE,
  pdfUrl: (path) => `${API_BASE}${path}`,
  getStatus: () => request("/api/status"),
  generateBlueprint: (candidate, tier, language) =>
    request("/api/intake/generate", {
      method: "POST",
      body: { candidate, tier, language },
      timeout: 180000, // generation can take a while
    }),
};
