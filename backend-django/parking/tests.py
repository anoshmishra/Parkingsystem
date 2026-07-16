from datetime import timedelta
from base64 import b64decode

from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch

from .models import Booking, ParkingLot, ParkingSlot, VehicleType
from .notifications import build_booking_receipt, send_booking_confirmation
from .services import BookingService


class ParkingServiceTests(TestCase):
    def setUp(self):
        self.car_type = VehicleType.objects.create(name="Test Car", slug="test-car", active=True)
        self.ev_type = VehicleType.objects.create(name="Test EV Car", slug="test-ev-car", active=True)
        self.lot = ParkingLot.objects.create(name="Downtown", address="Main Street", active=True)
        self.lot.vehicle_types.add(self.car_type, self.ev_type)
        self.slot = ParkingSlot.objects.create(parking_lot=self.lot, number=1, zone="A", floor=1)
        self.slot.vehicle_types.add(self.car_type)
        self.ev_slot = ParkingSlot.objects.create(parking_lot=self.lot, number=2, zone="A", floor=1)
        self.ev_slot.vehicle_types.add(self.ev_type)

    def test_lot_supports_vehicle_type(self):
        self.assertTrue(self.lot.supports_vehicle_type(self.car_type))
        self.assertTrue(self.lot.supports_vehicle_type(self.ev_type))

    def test_create_booking_rejects_duplicate_active_booking(self):
        Booking.objects.create(
            booking_id="B-1001",
            vehicle_number="OD02AB1234",
            vehicle_type=self.car_type,
            parking_lot=self.lot,
            slot=self.slot,
            status="reserved",
            reservation_expires_at=timezone.now() + timedelta(minutes=15),
            start_time=timezone.now(),
        )

        with self.assertRaises(ValueError):
            BookingService.create_booking(
                vehicle_number="OD02AB9999",
                owner_name="Test Owner",
                owner_email="owner@example.com",
                owner_phone="+919876543210",
                vehicle_type=self.car_type,
                parking_lot=self.lot,
                slot=self.slot,
                reservation_minutes=15,
            )

    def test_create_booking_rejects_slot_marked_reserved(self):
        self.slot.reserved = True
        self.slot.save(update_fields=["reserved"])

        with self.assertRaises(ValueError):
            BookingService.create_booking(
                vehicle_number="OD02AB9999",
                owner_name="Test Owner",
                owner_email="owner@example.com",
                owner_phone="+919876543210",
                vehicle_type=self.car_type,
                parking_lot=self.lot,
                slot=self.slot,
                reservation_minutes=15,
            )

    def test_available_slots_exclude_active_booking_even_when_slot_flag_is_stale(self):
        Booking.objects.create(
            booking_id="B-1002",
            vehicle_number="OD02AB5555",
            vehicle_type=self.ev_type,
            parking_lot=self.lot,
            slot=self.ev_slot,
            status="reserved",
            reservation_expires_at=timezone.now() + timedelta(minutes=15),
            start_time=timezone.now(),
        )

        response = self.client.get(f"/api/lots/{self.lot.pk}/slots/available/?vehicle_type={self.ev_type.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_lot_available_count_respects_vehicle_type_filter(self):
        Booking.objects.create(
            booking_id="B-1003",
            vehicle_number="OD02AB5555",
            vehicle_type=self.ev_type,
            parking_lot=self.lot,
            slot=self.ev_slot,
            status="reserved",
            reservation_expires_at=timezone.now() + timedelta(minutes=15),
            start_time=timezone.now(),
        )

        response = self.client.get(f"/api/lots/?vehicle_type={self.ev_type.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["available_slot_count"], 0)

    @patch("parking.views.send_booking_confirmation", return_value={"sent": True, "error": None})
    def test_booking_endpoint_captures_owner_details_and_sends_receipt(self, send_receipt):
        response = self.client.post(
            "/api/bookings/",
            {
                "vehicle_number": "OD02AB7777",
                "owner_name": "Aarav Kumar",
                "owner_email": "aarav@example.com",
                "owner_phone": "+91 98765 43210",
                "vehicle_type": self.car_type.pk,
                "parking_lot": self.lot.pk,
                "slot": self.slot.pk,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["owner_name"], "Aarav Kumar")
        self.assertEqual(response.json()["owner_email"], "aarav@example.com")
        self.assertTrue(response.json()["success"])
        self.assertTrue(response.json()["receipt_sent"])
        self.assertIsNone(response.json()["receipt_error"])
        self.assertEqual(response.json()["receipt_delivery"]["sent"], True)
        send_receipt.assert_called_once()

        list_response = self.client.get("/api/bookings/")
        self.assertEqual(list_response.status_code, 200)
        self.assertNotIn("owner_email", list_response.json()[0])

    def test_booking_receipt_is_a_pdf(self):
        booking = BookingService.create_booking(
            vehicle_number="OD02AB7777",
            owner_name="Aarav Kumar",
            owner_email="aarav@example.com",
            owner_phone="+919876543210",
            vehicle_type=self.car_type,
            parking_lot=self.lot,
            slot=self.slot,
        )

        receipt = build_booking_receipt(booking)

        self.assertTrue(receipt.startswith(b"%PDF"))

    @override_settings(
        SENDGRID_API_KEY="SG.test-key",
        DEFAULT_FROM_EMAIL="Parking Reservations <parking@example.com>",
        PARKING_DEVELOPER_EMAIL="anoshmishra09@gmail.com",
    )
    @patch("parking.notifications.SendGridAPIClient")
    def test_sendgrid_confirmation_contains_pdf_and_developer_bcc(self, client_class):
        booking = BookingService.create_booking(
            vehicle_number="OD02AB7777",
            owner_name="Aarav Kumar",
            owner_email="aarav@example.com",
            owner_phone="+919876543210",
            vehicle_type=self.car_type,
            parking_lot=self.lot,
            slot=self.slot,
        )
        client_class.return_value.client.mail.send.post.return_value.status_code = 202

        delivery = send_booking_confirmation(booking)

        self.assertEqual(delivery, {"sent": True, "error": None})
        request_body = client_class.return_value.client.mail.send.post.call_args.kwargs["request_body"]
        self.assertEqual(request_body["personalizations"][0]["to"], [{"email": "aarav@example.com"}])
        self.assertEqual(request_body["personalizations"][0]["bcc"], [{"email": "anoshmishra09@gmail.com"}])
        self.assertEqual(request_body["attachments"][0]["filename"], f"parking-receipt-{booking.booking_id}.pdf")
        self.assertTrue(b64decode(request_body["attachments"][0]["content"]).startswith(b"%PDF"))

    @override_settings(SENDGRID_API_KEY="SG.test-key")
    @patch("parking.notifications.SendGridAPIClient")
    def test_sendgrid_error_does_not_escape_the_booking_request(self, client_class):
        booking = BookingService.create_booking(
            vehicle_number="OD02AB7777",
            owner_name="Aarav Kumar",
            owner_email="aarav@example.com",
            owner_phone="+919876543210",
            vehicle_type=self.car_type,
            parking_lot=self.lot,
            slot=self.slot,
        )
        client_class.return_value.client.mail.send.post.side_effect = SystemExit("simulated failure")

        delivery = send_booking_confirmation(booking)

        self.assertFalse(delivery["sent"])
        self.assertEqual(delivery["error"], "SendGrid delivery stopped unexpectedly.")

    @patch(
        "parking.views.send_booking_confirmation",
        return_value={"sent": False, "error": "SendGrid rejected the request: invalid sender."},
    )
    def test_booking_succeeds_when_sendgrid_receipt_fails(self, send_receipt):
        response = self.client.post(
            "/api/bookings/",
            {
                "vehicle_number": "OD02AB7777",
                "owner_name": "Aarav Kumar",
                "owner_email": "aarav@example.com",
                "owner_phone": "+919876543210",
                "vehicle_type": self.car_type.pk,
                "parking_lot": self.lot.pk,
                "slot": self.slot.pk,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.json()["success"])
        self.assertFalse(response.json()["receipt_sent"])
        self.assertEqual(response.json()["receipt_error"], "SendGrid rejected the request: invalid sender.")
        send_receipt.assert_called_once()
