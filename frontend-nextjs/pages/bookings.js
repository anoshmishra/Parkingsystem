import { useEffect, useState } from "react";
import { fetchActiveBookingsReport, fetchBookings } from "../lib/api";

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [activeReport, setActiveReport] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchBookings(), fetchActiveBookingsReport()])
      .then(([bookingRows, reportRows]) => {
        setBookings(bookingRows);
        setActiveReport(reportRows);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main style={{ maxWidth: 900, margin: "20px auto", fontFamily: "sans-serif" }}>
      <h1>Bookings</h1>
      {error ? <p style={{ color: "red" }}>{error}</p> : null}

      <h3>Django Bookings API</h3>
      <pre>{JSON.stringify(bookings, null, 2)}</pre>

      <h3>Go Active Bookings Report</h3>
      <pre>{JSON.stringify(activeReport, null, 2)}</pre>
    </main>
  );
}
