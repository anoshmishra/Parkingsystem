from django.test import TestCase
from django.utils import timezone

from .models import Booking, ParkingLot, ParkingSlot, VehicleType
from .services import BookingService


class ParkingServiceTests(TestCase):
    def setUp(self):
        self.car_type = VehicleType.objects.create(name="Test Car", slug="test-car", active=True)
        self.ev_type = VehicleType.objects.create(name="Test EV Car", slug="test-ev-car", active=True)
        self.lot = ParkingLot.objects.create(name="Downtown", address="Main Street", active=True)
        self.lot.vehicle_types.add(self.car_type, self.ev_type)
        self.slot = ParkingSlot.objects.create(parking_lot=self.lot, number=1, zone="A", floor=1)
        self.slot.vehicle_types.add(self.car_type)

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
            reservation_expires_at=timezone.now() + timezone.timedelta(minutes=15),
            start_time=timezone.now(),
        )

        with self.assertRaises(ValueError):
            BookingService.create_booking(
                vehicle_number="OD02AB9999",
                vehicle_type=self.car_type,
                parking_lot=self.lot,
                slot=self.slot,
                reservation_minutes=15,
            )
