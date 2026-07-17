import { useEffect, useState } from "react";
import { fetchBookings } from "../lib/api";

function TyreLoader() {
  return (
    <div className="tyre-loader" role="status" aria-live="polite">
      <div className="tyre-wheel" aria-hidden="true">
        <div className="tyre-rim"><span /></div>
      </div>
      <div>
        <strong>Syncing live reservations</strong>
        <p>Updating the parking operations feed.</p>
      </div>
    </div>
  );
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    fetchBookings()
      .then((rows) => {
        if (active) setBookings(rows || []);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="shell">
      <div className="topbar">
        <div className="brand-lockup">
          <span className="brand-emblem" aria-hidden="true"><i /></span>
          <span>Park<span>Drive</span></span>
        </div>
        <div className="system-live"><span /> Operations live</div>
      </div>

      <section className="hero-card compact">
        <div>
          <p className="eyebrow">Operations command centre</p>
          <h1>Booking <em>intelligence.</em></h1>
          <p className="subtle">A live view of reservations moving through your parking network.</p>
        </div>
      </section>

      {error ? <div className="error-card">{error}</div> : null}

      <section className="card-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Live activity</p>
            <h2>Reservation feed</h2>
          </div>
          <div className="registration-pill"><span>Current</span>{loading ? "Syncing" : `${bookings.length} bookings`}</div>
        </div>

        {loading ? (
          <TyreLoader />
        ) : bookings.length ? (
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
          <div className="tyre-loader compact">
            <div className="tyre-wheel" aria-hidden="true"><div className="tyre-rim"><span /></div></div>
            <strong>No reservations are active right now.</strong>
          </div>
        )}
      </section>
    </main>
  );
}
