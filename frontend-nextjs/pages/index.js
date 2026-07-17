import { useEffect, useMemo, useState } from "react";
import { createBooking, fetchAvailableSlots, fetchLots, fetchVehicleTypes } from "../lib/api";

const STEPS = ["Vehicle details", "Choose parking", "Confirm booking"];

function TyreLoader({ label, compact = false }) {
  return (
    <div className={`tyre-loader ${compact ? "compact" : ""}`} role="status" aria-live="polite">
      <div className="tyre-wheel" aria-hidden="true">
        <div className="tyre-rim"><span /></div>
      </div>
      <div>
        <strong>{label}</strong>
        {!compact ? <p>Parking intelligence is working on it.</p> : null}
      </div>
    </div>
  );
}

function VehicleMark({ vehicleType }) {
  const name = vehicleType?.name?.toLowerCase() || "";
  const isLarge = /bus|truck|van|tractor|emergency/.test(name);
  const isTwoWheeler = /bike|bicycle|motorcycle|scooter/.test(name);

  return (
    <svg className={`vehicle-mark ${isLarge ? "large" : ""} ${isTwoWheeler ? "two-wheeler" : ""}`} viewBox="0 0 64 40" aria-hidden="true">
      {isTwoWheeler ? (
        <>
          <circle cx="16" cy="29" r="7" />
          <circle cx="48" cy="29" r="7" />
          <path d="M16 29h12l8-16h8m-13 0 7 16m-14-10h12" />
        </>
      ) : (
        <>
          <path d={isLarge ? "M5 14h45l8 8v9H5z" : "M7 21l7-10h27l10 10h6v10H7z"} />
          {!isLarge ? <path d="M19 12h19l7 9H12z" /> : <path d="M14 15v16m14-16v16m14-16v16" />}
          <circle cx="17" cy="31" r="5" />
          <circle cx="48" cy="31" r="5" />
        </>
      )}
    </svg>
  );
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return `₹${amount.toLocaleString("en-IN")}`;
}

export default function HomePage() {
  const [vehicleTypes, setVehicleTypes] = useState([]);
  const [lots, setLots] = useState([]);
  const [selectedVehicleType, setSelectedVehicleType] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerPhone, setOwnerPhone] = useState("");
  const [selectedLot, setSelectedLot] = useState(null);
  const [slots, setSlots] = useState([]);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [loadingLabel, setLoadingLabel] = useState("");
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
      })
      .finally(() => {
        if (active) setCatalogLoading(false);
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
    if (!ownerName.trim()) {
      setError("Enter the vehicle owner's name to continue.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(ownerEmail.trim())) {
      setError("Enter a valid owner email address to receive the receipt.");
      return;
    }
    if (!/^\+?[0-9][0-9 ()-]{6,23}$/.test(ownerPhone.trim())) {
      setError("Enter a valid owner phone number.");
      return;
    }

    try {
      setError("");
      setLoading(true);
      setLoadingLabel("Finding compatible parking");
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
      setLoadingLabel("");
    }
  }

  async function selectLot(lot) {
    setSelectedLot(lot);
    setError("");
    setBookingResult(null);
    setStatus({ type: "info", message: "Allocating the best available slot…" });
    setLoading(true);
    setLoadingLabel("Allocating your best bay");
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
      setLoadingLabel("");
    }
  }

  async function confirmBooking() {
    if (!selectedLot || !selectedVehicleType || !vehicleNumber.trim() || !ownerName.trim() || !ownerEmail.trim() || !ownerPhone.trim()) {
      setError("Complete the booking details before confirming.");
      return;
    }

    if (!bestAvailableSlot) {
      setError("No compatible slots are currently available for this lot.");
      return;
    }

    setLoading(true);
    setLoadingLabel("Securing your reservation");
    setError("");
    try {
      const response = await createBooking({
        vehicle_number: vehicleNumber.trim().toUpperCase(),
        owner_name: ownerName.trim(),
        owner_email: ownerEmail.trim().toLowerCase(),
        owner_phone: ownerPhone.trim(),
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
      setLoadingLabel("");
    }
  }

  return (
    <main className="shell">
      <div className="topbar">
        <div className="brand-lockup">
          <span className="brand-emblem" aria-hidden="true"><i /></span>
          <span>Park<span>Drive</span></span>
        </div>
        <div className="system-live"><span /> System online</div>
      </div>

      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">Connected parking network</p>
          <h1>Park smarter. <em>Drive easier.</em></h1>
          <p className="subtle">Vehicle-aware availability, intelligent bay allocation, and a receipt delivered the moment your reservation is confirmed.</p>
        </div>
        <div className="hero-dashboard" aria-label="Live parking status">
          <div className="dashboard-speed"><span>LIVE</span><strong>24<span>/7</span></strong><small>network access</small></div>
          <div className="dashboard-line" />
          <div className="dashboard-meta"><span>REAL-TIME</span><strong>Bay availability</strong><p>Secured & monitored</p></div>
        </div>
      </section>

      <section className="stepper">
        {STEPS.map((label, index) => (
          <div key={label} className={`step ${step === index + 1 ? "active" : ""} ${step > index + 1 ? "complete" : ""}`}>
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
            <div className="section-kicker"><span>01</span> Start your reservation</div>
            <h2>Tell us about your vehicle</h2>
            <div className="vehicle-number-field">
              <label className="field-label" htmlFor="vehicle-number">Registration number</label>
              <div className="plate-input">
                <span aria-hidden="true">IND</span>
                <input
                  id="vehicle-number"
                  className="field"
                  value={vehicleNumber}
                  onChange={(event) => setVehicleNumber(event.target.value.toUpperCase())}
                  placeholder="OD 02 AB 1234"
                  maxLength={20}
                />
              </div>
            </div>

            <div className="contact-section">
              <div>
                <p className="contact-heading">Vehicle owner details</p>
                <p className="subtle">We’ll email a PDF parking receipt to the owner once the slot is confirmed.</p>
              </div>
              <div className="owner-fields">
                <div>
                  <label className="field-label" htmlFor="owner-name">Owner Name</label>
                  <input
                    id="owner-name"
                    className="field"
                    value={ownerName}
                    onChange={(event) => setOwnerName(event.target.value)}
                    placeholder="Example: Priya Sharma"
                    autoComplete="name"
                    maxLength={120}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="owner-email">Owner Email</label>
                  <input
                    id="owner-email"
                    className="field"
                    type="email"
                    value={ownerEmail}
                    onChange={(event) => setOwnerEmail(event.target.value)}
                    placeholder="priya@example.com"
                    autoComplete="email"
                    maxLength={254}
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor="owner-phone">Phone Number</label>
                  <input
                    id="owner-phone"
                    className="field"
                    type="tel"
                    value={ownerPhone}
                    onChange={(event) => setOwnerPhone(event.target.value)}
                    placeholder="+91 98765 43210"
                    autoComplete="tel"
                    inputMode="tel"
                    maxLength={25}
                  />
                </div>
              </div>
            </div>

            <div className="vehicle-section-heading">
              <div>
                <label className="field-label">Vehicle class</label>
                <p className="subtle">Select the vehicle entering the facility.</p>
              </div>
              <span className="selection-count">{vehicleTypes.length} supported</span>
            </div>
            {catalogLoading ? (
              <TyreLoader label="Loading vehicle classes" />
            ) : (
              <div className="vehicle-grid">
                {vehicleTypes.map((vehicleType) => (
                  <button
                    key={vehicleType.id}
                    className={`vehicle-card ${selectedVehicleType === String(vehicleType.id) ? "selected" : ""}`}
                    onClick={() => chooseVehicleType(vehicleType.id)}
                  >
                    <VehicleMark vehicleType={vehicleType} />
                    <div>
                      <strong>{vehicleType.name}</strong>
                      <span>{vehicleType.description || "Flexible parking support"}</span>
                    </div>
                    <span className="selection-dot" aria-hidden="true" />
                  </button>
                ))}
              </div>
            )}

            <div className="actions">
              <button className="primary-btn" onClick={loadLots} disabled={loading}>
                {loading ? <TyreLoader label="Scanning" compact /> : <>Find parking <span aria-hidden="true">→</span></>}
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
              <div className="registration-pill"><span>Vehicle</span>{vehicleNumber}</div>
            </div>

            {loading ? (
              <TyreLoader label={loadingLabel || "Loading parking options"} />
            ) : (
              <div className="lot-grid">
                {lots.map((lot) => (
                  <button key={lot.id} className={`lot-card ${selectedLot?.id === lot.id ? "selected" : ""}`} onClick={() => selectLot(lot)}>
                    <div className="lot-topline">
                      <div>
                        <h3>{lot.name}</h3>
                        <p>{lot.address}</p>
                      </div>
                      {lot.recommended ? <span className="pill accent">Best match</span> : null}
                    </div>
                    <div className="meta-row">
                      <span><i className="status-dot" /> {lot.available_slot_count} bays open</span>
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
              <div className="registration-pill"><span>Destination</span>{selectedLot?.name || "Selected lot"}</div>
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
                  <p>Owner: {ownerName}</p>
                  <p>{ownerEmail} • {ownerPhone}</p>
                  <p>Reservation hold: 15 min</p>
                </div>
              </div>
            ) : null}

            {loading ? (
              <TyreLoader label={loadingLabel || "Preparing your reservation"} />
            ) : (
              <>
                <div className="slot-row">
                  {slots.length ? (
                    slots.slice(0, 8).map((slot) => (
                      <div key={slot.id} className={`slot-chip ${slot.id === bestAvailableSlot?.id ? "selected" : ""}`}>
                        <span>Bay</span> {slot.zone}-{slot.number}
                      </div>
                    ))
                  ) : (
                    <p className="subtle">No slots are currently available for this selection.</p>
                  )}
                </div>

                <div className="actions">
                  <button className="primary-btn" onClick={confirmBooking} disabled={!selectedLot || !bestAvailableSlot || loading || Boolean(bookingResult)}>
                    {bookingResult ? "Reservation confirmed" : <>Confirm reservation <span aria-hidden="true">→</span></>}
                  </button>
                </div>
              </>
            )}

            {bookingResult ? (
              <div className="confirmation-card">
                <div className="confirmation-badge"><span>✓</span> Reservation confirmed</div>
                <h3>Booking ID {bookingResult.booking_id}</h3>
                <p>Vehicle {bookingResult.vehicle_number} is parked securely at {selectedLot?.name}.</p>
                <p>Slot {bookingResult.slot?.number} • Floor {bookingResult.slot?.floor || 1}</p>
                <p>{bookingResult.receipt_delivery?.sent ? `A PDF receipt has been emailed to ${ownerEmail}.` : bookingResult.receipt_delivery?.message}</p>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </main>
  );
}
