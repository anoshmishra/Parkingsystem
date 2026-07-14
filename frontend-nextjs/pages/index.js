import { useEffect, useState } from "react";
import SlotGrid from "../components/SlotGrid";
import { API_BASE, fetchAvailableSlots, fetchLots } from "../lib/api";

const FILTERS = [
  { key: 'available', label: 'Available' },
  { key: 'occupied', label: 'Occupied' },
  { key: 'all', label: 'All' }
]

export default function HomePage() {
  const [lots, setLots] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedLot, setSelectedLot] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [statusTone, setStatusTone] = useState("info");
  const [loading, setLoading] = useState(false);
  const [lotsLoaded, setLotsLoaded] = useState(false);
  const [filter, setFilter] = useState('available');

  useEffect(() => {
    let isCurrent = true;

    fetchLots()
      .then((rows) => {
        if (!isCurrent) return;

        setLots(rows);
        setLotsLoaded(true);
        if (rows.length === 0) {
          setError("No parking lots found in the backend database. Run the seed command on the deployed Django service.");
        }
      })
      .catch((err) => {
        if (!isCurrent) return;

        console.error("Error fetching lots:", err);
        setLotsLoaded(true);
        setError(`Could not connect to Django backend at ${API_BASE}.`);
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  function handleLotChange(event) {
    setSelectedLot(event.target.value);
    setSlots([]);
    setError("");
  }

  async function loadSlots(forFilter = filter) {
    if (lotsLoaded && lots.length === 0) {
      setError("No parking lots found in the backend database. Run the seed command on the deployed Django service.");
      return;
    }
    if (!selectedLot) {
      setError("Please select a lot first");
      return;
    }
    try {
      setError("");
      setStatusMessage("");
      setLoading(true);
      const parsed = await fetchAvailableSlots(selectedLot, forFilter);
      setSlots(parsed);
    } catch (err) {
      setError("Failed to load slots: " + err.message);
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Parking Dashboard</h1>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 12 }}>
        <div>
          <label htmlFor="lot" style={{ fontWeight: '600', marginRight: 8 }}>Parking Lot</label>
          <select id="lot" value={selectedLot} onChange={handleLotChange} disabled={!lotsLoaded || lots.length === 0}>
            <option value="">{lotsLoaded && lots.length === 0 ? "No lots available" : "Select lot"}</option>
            {lots.map((lot) => (
              <option key={lot.id} value={lot.id}>{lot.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="vehicle" style={{ fontWeight: '600', marginRight: 8 }}>Vehicle / Number Plate</label>
          <input
            id="vehicle"
            type="text"
            placeholder="e.g. KA05AB1234 or AB-123"
            value={vehicleNumber}
            onChange={(e) => setVehicleNumber(e.target.value.toUpperCase())}
            maxLength={20}
            autoCapitalize="characters"
            spellCheck={false}
            style={{ width: 170, textTransform: 'uppercase' }}
          />
        </div>

        <div>
          <button onClick={() => loadSlots()} className="filter-btn" disabled={!lotsLoaded || lots.length === 0}>Load Slots</button>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {statusMessage ? <div className={`status-banner ${statusTone}`}>{statusMessage}</div> : null}

      <div className="filter-bar">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`filter-btn ${filter === f.key ? 'active' : ''}`}
            disabled={!lotsLoaded || lots.length === 0}
            onClick={() => { setFilter(f.key); loadSlots(f.key); }}
          >
            {f.label}
          </button>
        ))}
      </div>

      <hr style={{ margin: '18px 0', border: 0, borderTop: '1px solid #eee' }} />

      <h3>Slots</h3>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 60 }}></div>
          ))}
        </div>
      ) : (
        slots.length > 0 ? (
          <SlotGrid
            slots={slots}
            vehicleNumber={vehicleNumber}
            fetchSlots={() => loadSlots()}
            onStatus={({ type, message }) => {
              setStatusTone(type === 'error' ? 'error' : 'success');
              setStatusMessage(message);
            }}
          />
        ) : (
          <p className="small-muted">No slots loaded. Select a lot and click "Load Slots".</p>
        )
      )}
    </main>
  );
}
