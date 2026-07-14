import { createBooking } from "../lib/api";

export default function SlotGrid({ slots, vehicleNumber, fetchSlots, onStatus }) {
  async function handleBook(slotId) {
    const plate = vehicleNumber.trim();
    if (!plate) {
      onStatus?.({ type: 'error', message: 'Please enter a vehicle number first.' });
      return;
    }

    try {
      const response = await createBooking({
        vehicle_number: plate,
        slot: slotId,
        start_time: new Date().toISOString()
      });

      const slotLabel = slots.find((entry) => entry.id === slotId)?.number;
      onStatus?.({ type: 'success', message: `Booked ${plate} into Slot ${slotLabel || slotId}.` });
      if (fetchSlots) await fetchSlots();
    } catch (err) {
      console.error("Booking Error:", err);
      onStatus?.({ type: 'error', message: err.message || "Failed to create booking" });
    }
  }

  if (!slots || !slots.length) return <p className="small-muted">No slots available for this lot.</p>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginTop: 16 }}>
      {slots.map((slot) => (
        <button
          key={slot.id}
          onClick={() => !slot.is_occupied && handleBook(slot.id)}
          disabled={slot.is_occupied}
          className="slot-btn"
        >
          <div style={{ fontWeight: 700 }}>Slot {slot.number}</div>
          <div style={{ marginTop: 6, fontSize: '0.9rem' }}>
            {slot.is_occupied ? <span style={{ color: '#b00' }}>Occupied</span> : <span style={{ color: '#000' }}>Available</span>}
          </div>
        </button>
      ))}
    </div>
  );
}
