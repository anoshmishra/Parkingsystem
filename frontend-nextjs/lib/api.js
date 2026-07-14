const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_DJANGO_API_BASE ||
  "https://parking-backend-22m3.onrender.com";

async function readJsonResponse(res, fallbackMessage) {
  let json = null;
  try {
    json = await res.json();
  } catch {
    // Some failures return an empty body or plain text.
  }

  if (!res.ok) {
    throw new Error(json?.message || fallbackMessage);
  }

  return json;
}

export async function fetchLots() {
  const res = await fetch(`${API_BASE}/api/lots/`);
  return readJsonResponse(res, "Failed to fetch lots");
}

export async function fetchAvailableSlots(lotId, filter = 'available') {
  const url = new URL(`${API_BASE}/api/lots/${lotId}/slots/available/`);
  if (filter) url.searchParams.set('filter', filter);

  const res = await fetch(url.toString());
  return readJsonResponse(res, "Failed to fetch slots");
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
