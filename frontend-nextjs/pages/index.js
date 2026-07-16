import { useEffect, useMemo, useState } from "react";
import { createBooking, fetchAvailableSlots, fetchLots, fetchVehicleTypes } from "../lib/api";

const STEPS = ["Vehicle details", "Choose parking", "Confirm booking"];

function formatCurrency(value) {
  const amount = Number(value || 0);
  return `₹${amount.toLocaleString("en-IN")}`;
}

export default function HomePage() {
  const [vehicleTypes, setVehicleTypes] = useState([]);
  const [lots, setLots] = useState([]);
  const [selectedVehicleType, setSelectedVehicleType] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [selectedLot, setSelectedLot] = useState(null);
  const [slots, setSlots] = useState([]);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState({ type: "info", message: "" });
  const [bookingResult, setBookingResult] = useState(null);

  const activeVehicleType = useMemo(
    () => vehicleTypes.find((entry) => entry.id === Number(selectedVehicleType)) || null,
    [selectedVehicleType, vehicleTypes]
  );
  const bestAvailableSlot = useMemo(
    () => slots.find((slot) => !slot.is_occupied && !slot.reserved && !slot.maintenance && !slot.disabled) || null,
    [slots]
  );

  useEffect(() => {
    let active = true;

    fetchVehicleTypes()
      .then((rows) => {
        if (!active) return;
        setVehicleTypes(rows || []);
        if (rows?.[0]) {
          setSelectedVehicleType(String(rows[0].id));
        } else {
          setStatus({ type: "info", message: "No active vehicle types are configured yet." });
        }
      })
      .catch(() => {
        if (!active) return;
        setError("Unable to load vehicle types right now.");
      });

    return () => {
      active = false;
    };
  }, []);

  function chooseVehicleType(vehicleTypeId) {
    setSelectedVehicleType(String(vehicleTypeId));
    setSelectedLot(null);
    setLots([]);
    setSlots([]);
    setBookingResult(null);
    setStatus({ type: "info", message: "" });
    if (step > 1) {
      setStep(1);
    }
  }

  async function loadLots() {
    if (!selectedVehicleType) {
      setError("Please select a vehicle type first.");
      return;
    }
    if (!vehicleNumber.trim()) {
      setError("Enter a vehicle number to continue.");
      return;
    }

    try {
      setError("");
      setLoading(true);
      const rows = await fetchLots(selectedVehicleType);
      setLots(rows || []);
      setSelectedLot(null);
      setSlots([]);
      setBookingResult(null);
      setStatus(
        rows?.length
          ? { type: "info", message: "Choose a compatible parking lot to see available slots." }
          : { type: "info", message: "No compatible parking lots are available for this vehicle type yet." }
      );
      setStep(2);
    } catch (err) {
      setError(err.message || "Failed to load parking lots.");
    } finally {
      setLoading(false);
    }
  }

  async function selectLot(lot) {
    setSelectedLot(lot);
    setError("");
    setBookingResult(null);
    setStatus({ type: "info", message: "Allocating the best available slot…" });
    setLoading(true);
    try {
      const rows = await fetchAvailableSlots(lot.id, "available", selectedVehicleType);
      setSlots(rows || []);
      setStatus(
        rows?.length
          ? { type: "info", message: `Best slot ready: ${rows[0].zone}-${rows[0].number}.` }
          : { type: "info", message: "No compatible slots are currently available for this lot." }
      );
      setStep(3);
    } catch (err) {
      setError(err.message || "Unable to load slots for this lot.");
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }

  async function confirmBooking() {
    if (!selectedLot || !selectedVehicleType || !vehicleNumber.trim()) {
      setError("Complete the booking details before confirming.");
      return;
    }

    if (!bestAvailableSlot) {
      setError("No compatible slots are currently available for this lot.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const response = await createBooking({
        vehicle_number: vehicleNumber.trim().toUpperCase(),
        vehicle_type: Number(selectedVehicleType),
        parking_lot: selectedLot.id,
        slot: bestAvailableSlot.id,
        reservation_minutes: 15,
      });
      setBookingResult(response);
      setSlots((currentSlots) => currentSlots.filter((slot) => slot.id !== bestAvailableSlot.id));
      setStatus({ type: "success", message: "Booking confirmed. Your reservation is active." });
      setStep(3);
    } catch (err) {
      setError(err.message || "Booking could not be created.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Smart multi-vehicle parking</p>
          <h1>Reserve a premium parking experience in minutes.</h1>
          <p className="subtle">Guided booking flow, vehicle-aware lot filtering, and instant slot allocation.</p>
        </div>
        <div className="hero-badge">Live availability</div>
      </section>

      <section className="stepper">
        {STEPS.map((label, index) => (
          <div key={label} className={`step ${step >= index + 1 ? "active" : ""}`}>
            <span>{index + 1}</span>
            <strong>{label}</strong>
          </div>
        ))}
      </section>

      {error ? <div className="error-card">{error}</div> : null}
      {status.message ? <div className={`status-banner ${status.type}`}>{status.message}</div> : null}

      {step === 1 ? (
        <section className="card-stack">
          <div className="card-panel">
            <h2>Step 1 • Vehicle details</h2>
            <label className="field-label" htmlFor="vehicle-number">Vehicle Number</label>
            <input
              id="vehicle-number"
              className="field"
              value={vehicleNumber}
              onChange={(event) => setVehicleNumber(event.target.value.toUpperCase())}
              placeholder="Example: OD02AB1234"
              maxLength={20}
            />

            <label className="field-label">Vehicle Type</label>
            <div className="vehicle-grid">
              {vehicleTypes.map((vehicleType) => (
                <button
                  key={vehicleType.id}
                  className={`vehicle-card ${selectedVehicleType === String(vehicleType.id) ? "selected" : ""}`}
                  onClick={() => chooseVehicleType(vehicleType.id)}
                >
                  <strong>{vehicleType.name}</strong>
                  <span>{vehicleType.description || "Flexible parking support"}</span>
                </button>
              ))}
            </div>

            <div className="actions">
              <button className="primary-btn" onClick={loadLots} disabled={loading}>
                {loading ? "Searching…" : "Continue to parking options"}
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {step >= 2 ? (
        <section className="card-stack">
          <div className="card-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 2 • Choose parking</p>
                <h2>{activeVehicleType?.name || "Selected vehicle"} parking options</h2>
              </div>
              <div className="pill">{vehicleNumber}</div>
            </div>

            {loading && !selectedLot ? (
              <div className="skeleton-grid">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="skeleton-card" />
                ))}
              </div>
            ) : (
              <div className="lot-grid">
                {lots.map((lot) => (
                  <button key={lot.id} className={`lot-card ${selectedLot?.id === lot.id ? "selected" : ""}`} onClick={() => selectLot(lot)}>
                    <div className="lot-topline">
                      <div>
                        <h3>{lot.name}</h3>
                        <p>{lot.address}</p>
                      </div>
                      {lot.recommended ? <span className="pill accent">Recommended</span> : null}
                    </div>
                    <div className="meta-row">
                      <span>Available slots • {lot.available_slot_count}</span>
                      <span>{formatCurrency(lot.price_hint)}</span>
                    </div>
                    <div className="meta-row small">
                      <span>{lot.is_covered ? "Covered" : "Open"}</span>
                      <span>{lot.is_ev_charging ? "EV charging" : "Standard"}</span>
                      <span>{lot.is_24x7 ? "24/7" : "Limited"}</span>
                    </div>
                    <div className="meta-row small">
                      <span>Security {lot.security_rating}/5</span>
                      <span>{lot.walking_time_minutes} min walk</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </section>
      ) : null}

      {step >= 3 ? (
        <section className="card-stack">
          <div className="card-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Step 3 • Confirm reservation</p>
                <h2>Your booking summary</h2>
              </div>
              <div className="pill">{selectedLot?.name || "Selected lot"}</div>
            </div>

            {selectedLot ? (
              <div className="summary-grid">
                <div className="summary-card">
                  <h3>Parking</h3>
                  <p>{selectedLot.name}</p>
                  <p>{selectedLot.address}</p>
                  <p>Security rating: {selectedLot.security_rating}/5</p>
                </div>
                <div className="summary-card">
                  <h3>Vehicle</h3>
                  <p>{vehicleNumber}</p>
                  <p>{activeVehicleType?.name}</p>
                  <p>Reservation window: 15 min</p>
                </div>
              </div>
            ) : null}

            {loading ? (
              <div className="skeleton-card large" />
            ) : (
              <>
                <div className="slot-row">
                  {slots.length ? (
                    slots.slice(0, 8).map((slot) => (
                      <div key={slot.id} className={`slot-chip ${slot.id === bestAvailableSlot?.id ? "selected" : ""}`}>
                        Slot {slot.number} • {slot.zone}
                      </div>
                    ))
                  ) : (
                    <p className="subtle">No slots are currently available for this selection.</p>
                  )}
                </div>

                <div className="actions">
                  <button className="primary-btn" onClick={confirmBooking} disabled={!selectedLot || !bestAvailableSlot || loading || Boolean(bookingResult)}>
                    {bookingResult ? "Booking confirmed" : "Confirm booking"}
                  </button>
                </div>
              </>
            )}

            {bookingResult ? (
              <div className="confirmation-card">
                <div className="confirmation-badge">Booking confirmed</div>
                <h3>Booking ID {bookingResult.booking_id}</h3>
                <p>Vehicle {bookingResult.vehicle_number} is parked securely at {selectedLot?.name}.</p>
                <p>Slot {bookingResult.slot?.number} • Floor {bookingResult.slot?.floor || 1}</p>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </main>
  );
}
