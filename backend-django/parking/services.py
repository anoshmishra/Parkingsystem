import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Booking, ParkingLot, ParkingSlot, Vehicle, VehicleType


VEHICLE_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9\- ]{2,20}$")


class BookingService:
    @staticmethod
    def validate_vehicle_number(vehicle_number):
        if not vehicle_number:
            raise ValueError("Vehicle number is required")
        normalized = vehicle_number.strip().upper()
        if not VEHICLE_NUMBER_PATTERN.match(normalized):
            raise ValueError("Vehicle number format is invalid")
        return normalized

    @staticmethod
    def create_booking(
        vehicle_number,
        owner_name,
        owner_email,
        owner_phone,
        vehicle_type,
        parking_lot,
        slot,
        reservation_minutes=15,
    ):
        if not isinstance(vehicle_type, VehicleType):
            vehicle_type = VehicleType.objects.filter(pk=vehicle_type).first()
        if not isinstance(parking_lot, ParkingLot):
            parking_lot = ParkingLot.objects.filter(pk=parking_lot).first()
        if not isinstance(slot, ParkingSlot):
            slot = ParkingSlot.objects.filter(pk=slot).first()

        if not vehicle_type or not parking_lot or not slot:
            raise ValueError("Invalid vehicle type, parking lot, or slot")

        normalized_vehicle_number = BookingService.validate_vehicle_number(vehicle_number)

        with transaction.atomic():
            slot = ParkingSlot.objects.select_for_update().get(pk=slot.pk)
            if not parking_lot.supports_vehicle_type(vehicle_type):
                raise ValueError("This parking lot does not support the selected vehicle type")
            if not slot.supports_vehicle_type(vehicle_type):
                raise ValueError("This slot does not support the selected vehicle type")
            if slot.parking_lot_id != parking_lot.pk:
                raise ValueError("Selected slot does not belong to the selected parking lot")
            if slot.disabled or slot.maintenance:
                raise ValueError("Selected slot is unavailable")
            if slot.is_occupied or slot.reserved:
                raise ValueError("Slot is already reserved")

            existing_active_booking = Booking.objects.filter(
                slot=slot,
                status__in=["reserved", "checked_in"],
                end_time__isnull=True,
            ).exists()
            if existing_active_booking:
                raise ValueError("Slot is already reserved")

            vehicle, _ = Vehicle.objects.get_or_create(number_plate=normalized_vehicle_number)
            vehicle.vehicle_type = vehicle_type
            vehicle.save(update_fields=["vehicle_type"])

            booking = Booking.objects.create(
                vehicle_number=normalized_vehicle_number,
                owner_name=owner_name.strip(),
                owner_email=owner_email.strip().lower(),
                owner_phone=owner_phone.strip(),
                vehicle_type=vehicle_type,
                parking_lot=parking_lot,
                slot=slot,
                status="reserved",
                payment_status="pending",
                start_time=timezone.now(),
                reservation_expires_at=timezone.now() + timedelta(minutes=reservation_minutes),
                duration_minutes=reservation_minutes,
            )
            slot.is_occupied = True
            slot.reserved = True
            slot.save(update_fields=["is_occupied", "reserved"])
            return booking

    @staticmethod
    def expire_reservations():
        now = timezone.now()
        expired = Booking.objects.filter(status="reserved", reservation_expires_at__lt=now, end_time__isnull=True)
        count = 0
        for booking in expired:
            booking.status = "expired"
            booking.end_time = now
            booking.save(update_fields=["status", "end_time"])
            booking.slot.is_occupied = False
            booking.slot.reserved = False
            booking.slot.save(update_fields=["is_occupied", "reserved"])
            count += 1
        return count
