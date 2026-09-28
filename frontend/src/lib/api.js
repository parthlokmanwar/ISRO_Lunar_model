/** Thin fetch wrapper. Vite proxies /api and /static to the backend in dev. */

async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body; keep the status line */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  scenarios: () => request('/api/scenarios'),

  match: (settings) =>
    request('/api/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }),

  analytics: (resultId) => request(`/api/analytics/${resultId}`),

  examples: () => request('/api/examples'),

  chat: (messages, context) =>
    request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, context }),
    }),

  csvUrl: (resultId) => `/api/export/csv/${resultId}`,
  jsonUrl: (resultId) => `/api/export/json/${resultId}`,
};
