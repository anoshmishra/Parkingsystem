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
	BookingID   int    `json:"booking_id"`
	NumberPlate string `json:"number_plate"`
	SlotNumber  int    `json:"slot_number"`
	LotName     string `json:"lot_name"`
	StartTime   string `json:"start_time"`
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
		SELECT b.id, v.number_plate, s.number, l.name, b.start_time::text
		FROM parking_booking b
		JOIN parking_vehicle v ON b.vehicle_id = v.id
		JOIN parking_slot s ON b.slot_id = s.id
		JOIN parking_parkinglot l ON s.lot_id = l.id
		WHERE b.end_time IS NULL
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
		if err := rows.Scan(&row.BookingID, &row.NumberPlate, &row.SlotNumber, &row.LotName, &row.StartTime); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		result = append(result, row)
	}

	respondJSON(w, result)
}

func occupancyHandler(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	rows, err := db.Query(`
		SELECT l.id, l.name, COUNT(s.id) FILTER (WHERE s.is_occupied = true) AS occupied_count
		FROM parking_parkinglot l
		LEFT JOIN parking_slot s ON l.id = s.lot_id
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