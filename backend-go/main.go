package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"os"

	_ "github.com/lib/pq"
)

type ActiveBooking struct {
	ID            int    `json:"id"`
	BookingID     string `json:"booking_id"`
	VehicleNumber string `json:"vehicle_number"`
	VehicleType   string `json:"vehicle_type"`
	SlotNumber    int    `json:"slot_number"`
	LotName       string `json:"lot_name"`
	StartTime     string `json:"start_time"`
	Status        string `json:"status"`
}

type OccupancyRow struct {
	LotID         int    `json:"lot_id"`
	LotName       string `json:"lot_name"`
	OccupiedSlots int    `json:"occupied_slots"`
}

func main() {
	db, err := sql.Open("postgres", getDSN())
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	http.HandleFunc("/active-bookings", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		activeBookingsHandler(w, r, db)
	})
	http.HandleFunc("/occupancy", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		occupancyHandler(w, r, db)
	})

	log.Println("Go API listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func getDSN() string {
	dsn := os.Getenv("GO_DB_DSN")
	if dsn != "" {
		return dsn
	}
	return "host=localhost port=5432 user=parking_user password=parking_pass dbname=parking_db sslmode=disable"
}

func activeBookingsHandler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	rows, err := db.Query(`
		SELECT
			b.id,
			b.booking_id,
			b.vehicle_number,
			vt.name,
			s.number,
			l.name,
			b.start_time::text,
			b.status
		FROM parking_booking b
		JOIN parking_vehicletype vt ON b.vehicle_type_id = vt.id
		JOIN parking_parkingslot s ON b.slot_id = s.id
		JOIN parking_parkinglot l ON b.parking_lot_id = l.id
		WHERE b.end_time IS NULL
			AND b.status IN ('reserved', 'checked_in')
		ORDER BY b.start_time DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	result := []ActiveBooking{}
	for rows.Next() {
		var row ActiveBooking
		if err := rows.Scan(
			&row.ID,
			&row.BookingID,
			&row.VehicleNumber,
			&row.VehicleType,
			&row.SlotNumber,
			&row.LotName,
			&row.StartTime,
			&row.Status,
		); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		result = append(result, row)
	}

	respondJSON(w, result)
}

func occupancyHandler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	rows, err := db.Query(`
		SELECT
			l.id,
			l.name,
			COUNT(DISTINCT s.id) FILTER (
				WHERE s.is_occupied = TRUE
					OR s.reserved = TRUE
					OR b.id IS NOT NULL
			) AS occupied_count
		FROM parking_parkinglot l
		LEFT JOIN parking_parkingslot s ON l.id = s.parking_lot_id
		LEFT JOIN parking_booking b
			ON b.slot_id = s.id
			AND b.end_time IS NULL
			AND b.status IN ('reserved', 'checked_in')
		GROUP BY l.id, l.name
		ORDER BY l.id
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	result := []OccupancyRow{}
	for rows.Next() {
		var row OccupancyRow
		if err := rows.Scan(&row.LotID, &row.LotName, &row.OccupiedSlots); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		result = append(result, row)
	}

	respondJSON(w, result)
}

func respondJSON(w http.ResponseWriter, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
