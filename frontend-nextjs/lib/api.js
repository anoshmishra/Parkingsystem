const rawApiBase =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.NEXT_PUBLIC_DJANGO_API_BASE ||
  "https://parking-backend-22m3.onrender.com";

// Keep the full backend URL for server-side calls, but use a same-origin proxy
// on the client to avoid CORS restrictions when the frontend is deployed.
const API_BASE_SERVER = rawApiBase.replace(/\/+$/, "");
export const API_BASE = typeof window === "undefined" ? API_BASE_SERVER : "";

function buildApiUrl(path, params = {}) {
  const base = API_BASE || "";
  const url = new URL(`${base}${path}`, typeof window === "undefined" ? "http://next-proxy.invalid" : window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function readJsonResponse(res, fallbackMessage) {
  let json = null;
  try {
    json = await res.json();
  } catch (error) {
    // Some failures return an empty body or plain text.
  }

  if (!res.ok) {
    throw new Error(json?.message || json?.detail || fallbackMessage);
  }

  return json;
}

export async function fetchVehicleTypes() {
  const res = await fetch(buildApiUrl("/api/vehicle-types/"));
  return readJsonResponse(res, "Failed to fetch vehicle types");
}

export async function fetchLots(vehicleType = "") {
  const url = buildApiUrl("/api/lots/", vehicleType ? { vehicle_type: vehicleType } : {});
  const res = await fetch(url);
  return readJsonResponse(res, "Failed to fetch lots");
}

export async function fetchAvailableSlots(lotId, filter = "available", vehicleType = "") {
  const params = { filter, vehicle_type: vehicleType };
  const res = await fetch(buildApiUrl(`/api/lots/${lotId}/slots/available/`, params));
  return readJsonResponse(res, "Failed to fetch slots");
}

export async function createBooking(payload) {
  const res = await fetch(buildApiUrl("/api/bookings/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJsonResponse(res, "Failed to create booking");
}

export async function fetchBookings() {
  const res = await fetch(buildApiUrl("/api/bookings/"));
  return readJsonResponse(res, "Failed to fetch bookings");
}
