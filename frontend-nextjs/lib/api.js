const rawApiBase =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_DJANGO_API_BASE ||
  "https://parking-backend-22m3.onrender.com";

// Keep the full backend URL for server-side calls, but use a same-origin proxy
// on the client to avoid CORS restrictions when the frontend is deployed.
const API_BASE_SERVER = rawApiBase.replace(/\/+$/, "");
export const API_BASE = typeof window === 'undefined' ? API_BASE_SERVER : "";

async function readJsonResponse(res, fallbackMessage) {
  let json = null;
  try {
    // Log raw response status for debugging
    // (kept minimal; removed in production if desired)
    // eslint-disable-next-line no-console
    console.log('[api] raw response status', res.status, res.url);
    json = await res.json();
    // eslint-disable-next-line no-console
    console.log('[api] parsed json', json);
  } catch (err) {
    // Some failures return an empty body or plain text.
    // eslint-disable-next-line no-console
    console.warn('[api] failed to parse JSON body', err && err.message);
  }

  if (!res.ok) {
    throw new Error(json?.message || json?.detail || fallbackMessage);
  }

  return json;
}

export async function fetchLots() {
  // Client-side: this will hit the Next.js proxy at `/api/lots`
  const url = `${API_BASE}/api/lots/`;
  // eslint-disable-next-line no-console
  console.log('[api] fetching lots from', url);
  const res = await fetch(url);
  const parsed = await readJsonResponse(res, "Failed to fetch lots");
  // eslint-disable-next-line no-console
  console.log('[api] fetchLots result', parsed);
  return parsed;
}

export async function fetchAvailableSlots(lotId, filter = 'available') {
  // Build a same-origin path for client and absolute URL for server-side
  const base = API_BASE || '';
  let path = `${base}/api/lots/${lotId}/slots/available/`;
  if (filter) {
    const qs = new URLSearchParams({ filter }).toString();
    path = `${path}?${qs}`;
  }

  // eslint-disable-next-line no-console
  console.log('[api] fetching slots from', path);
  const res = await fetch(path);
  const parsed = await readJsonResponse(res, "Failed to fetch slots");
  // eslint-disable-next-line no-console
  console.log('[api] fetchAvailableSlots result', parsed);
  return parsed;
}

export async function createBooking(payload) {
  const res = await fetch(`${API_BASE}/api/bookings/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return readJsonResponse(res, "Failed to create booking");
}

export async function fetchBookings() {
  const res = await fetch(`${API_BASE}/api/bookings/`);
  return readJsonResponse(res, "Failed to fetch bookings");
}

export async function fetchActiveBookingsReport() {
  const res = await fetch(`${API_BASE}/api/bookings/`);
  return readJsonResponse(res, "Failed to fetch active bookings report");
}
