import { createBooking } from "../lib/api";

export default function SlotGrid({ slots, selectedVehicle, fetchSlots }) {
  async function handleBook(slotId) {
    if (!selectedVehicle) {
      alert("Please enter a Vehicle ID in the input box first!");
      return;
    }

    try {
      // We send the ID and a current timestamp to satisfy Django's model requirements
      await createBooking({
        vehicle: Number(selectedVehicle),
        slot: slotId,
        start_time: new Date().toISOString()
      });

      alert("Booking created successfully!");
      
      // Refresh the parent state so the slot correctly shows as "Occupied"
      if (fetchSlots) {
        await fetchSlots();
      }
    } catch (err) {
      // If Django returns a 400, this alert will now show the SPECIFIC field error
      console.error("Booking Error:", err);
      alert("Failed to create booking: " + err.message);
    }
  }

  if (!slots.length) {
    return <p style={{ color: "#666", fontStyle: "italic" }}>No slots available for this lot.</p>;
  }

  return (
    <div style={{ 
      display: "grid", 
      gap: "12px", 
      gridTemplateColumns: "repeat(3, 1fr)",
      marginTop: "20px" 
    }}>
      {slots.map((slot) => (
        <button
          key={slot.id}
          onClick={() => !slot.is_occupied && handleBook(slot.id)}
          disabled={slot.is_occupied}
          style={{
            padding: "15px",
            borderRadius: "8px",
            border: "1px solid #ddd",
            cursor: slot.is_occupied ? "not-allowed" : "pointer",
            backgroundColor: slot.is_occupied ? "#f8d7da" : "#d4edda",
            color: slot.is_occupied ? "#721c24" : "#155724",
            transition: "transform 0.1s ease",
            fontWeight: "bold"
          }}
        >
          <div>Slot {slot.number}</div>
          <div style={{ fontSize: "0.8rem", fontWeight: "normal" }}>
            {slot.is_occupied ? "Occupied" : "Click to Book"}
          </div>
        </button>
      ))}
    </div>
  );
}