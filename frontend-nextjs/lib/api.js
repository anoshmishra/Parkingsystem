const API_DJANGO_BASE = "http://localhost:8001/api";
const API_GO_BASE = "http://localhost:8080";

export async function fetchLots() {
  const res = await fetch(`${API_DJANGO_BASE}/lots/`);
  if (!res.ok) throw new Error("Failed to fetch lots");
  return res.json();
}

export async function fetchAvailableSlots(lotId) {
  const res = await fetch(`${API_DJANGO_BASE}/lots/${lotId}/slots/available/`);
  if (!res.ok) throw new Error("Failed to fetch slots");
  return res.json();
}

export async function createBooking(payload) {
  const res = await fetch(`${API_DJANGO_BASE}/bookings/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error("Failed to create booking");
  return res.json();
}

export async function fetchBookings() {
  const res = await fetch(`${API_DJANGO_BASE}/bookings/`);
  if (!res.ok) throw new Error("Failed to fetch bookings");
  return res.json();
}

export async function fetchActiveBookingsReport() {
  const res = await fetch(`${API_GO_BASE}/active-bookings`);
  if (!res.ok) throw new Error("Failed to fetch active bookings report");
  return res.json();
}
