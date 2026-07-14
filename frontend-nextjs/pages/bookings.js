import { useEffect, useState } from "react";
import { fetchBookings } from "../lib/api";

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchBookings()
      .then((rows) => setBookings(rows || []))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="shell">
      <section className="hero-card compact">
        <div>
          <p className="eyebrow">Operations</p>
          <h1>Booking intelligence</h1>
          <p className="subtle">Live reservation activity and status trends for your parking network.</p>
        </div>
      </section>

      {error ? <div className="error-card">{error}</div> : null}

      <section className="card-panel">
        {bookings.length ? (
          <div className="booking-list">
            {bookings.map((booking) => (
              <article key={booking.id} className="booking-card">
                <div>
                  <div className="booking-title-row">
                    <strong>{booking.booking_id}</strong>
                    <span className={`pill ${booking.status === "reserved" ? "accent" : ""}`}>{booking.status}</span>
                  </div>
                  <p>{booking.vehicle_number} • {booking.vehicle_type?.name}</p>
                  <p>{booking.parking_lot?.name} • Slot {booking.slot?.number}</p>
                </div>
                <div className="booking-meta">
                  <span>Started {new Date(booking.start_time).toLocaleString()}</span>
                  <span>Expires {booking.reservation_expires_at ? new Date(booking.reservation_expires_at).toLocaleString() : "—"}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="subtle">No bookings have been recorded yet.</p>
        )}
      </section>
    </main>
  );
}
