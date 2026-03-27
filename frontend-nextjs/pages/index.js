import { useEffect, useState } from "react";
import SlotGrid from "../components/SlotGrid";
import { fetchAvailableSlots, fetchLots } from "../lib/api";

export default function HomePage() {
  const [lots, setLots] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedLot, setSelectedLot] = useState("");
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchLots()
      .then(setLots)
      .catch((err) => {
        console.error("Error fetching lots:", err);
        setError("Could not connect to Django backend. Ensure it is running on port 8001.");
      });
  }, []);

  async function loadSlots() {
    if (!selectedLot) {
      setError("Please select a lot first");
      return;
    }
    try {
      setError("");
      // Ensure we pass the selectedLot ID correctly
      const parsed = await fetchAvailableSlots(selectedLot);
      setSlots(parsed);
    } catch (err) {
      setError("Failed to load slots: " + err.message);
    }
  }

  return (
    <main style={{ maxWidth: 800, margin: "20px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1>Parking Management Dashboard</h1>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="lot" style={{ fontWeight: 'bold' }}>Parking Lot: </label>
        <select 
          id="lot" 
          value={selectedLot} 
          onChange={(e) => setSelectedLot(e.target.value)}
          style={{ padding: "5px", marginLeft: "10px" }}
        >
          <option value="">Select lot</option>
          {lots.map((lot) => (
            <option key={lot.id} value={lot.id}>
              {lot.name}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: 12 }}>
        <label htmlFor="vehicle" style={{ fontWeight: 'bold' }}>Vehicle ID: </label>
        <input
          id="vehicle"
          type="number"
          placeholder="e.g. 5"
          value={selectedVehicle}
          onChange={(e) => setSelectedVehicle(e.target.value)}
          style={{ padding: "5px", marginLeft: "10px", width: "60px" }}
        />
      </div>

      <button 
        onClick={loadSlots}
        style={{ padding: "8px 16px", cursor: "pointer", backgroundColor: "#0070f3", color: "white", border: "none", borderRadius: "4px" }}
      >
        Load Available Slots
      </button>

      {error ? (
        <div style={{ backgroundColor: "#ffeeee", border: "1px solid red", padding: "10px", marginTop: "15px", borderRadius: "4px" }}>
          <p style={{ color: "red", margin: 0 }}>{error}</p>
        </div>
      ) : null}

      <hr style={{ margin: "30px 0", border: "0", borderTop: "1px solid #eaeaea" }} />

      <h3>Slots</h3>
      {slots.length > 0 ? (
        <SlotGrid 
          slots={slots} 
          selectedVehicle={parseInt(selectedVehicle)} 
          fetchSlots={loadSlots} 
        />
      ) : (
        <p style={{ color: "#666" }}>No slots loaded. Select a lot and click the button above.</p>
      )}
    </main>
  );
}