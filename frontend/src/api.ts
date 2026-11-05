export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch("/api" + path, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let message = "The server could not complete this request.";
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // A plain HTTP error page still receives the friendly fallback.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch("/api" + path, { method: "POST" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "The server could not complete this request.");
  return payload as T;
}
