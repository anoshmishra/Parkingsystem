from django.core.management.base import BaseCommand
from django.utils import timezone

from parking.models import Booking, Facility, ParkingLot, ParkingSlot, Vehicle, VehicleType


DEFAULT_LOTS = (
    ("Downtown Lot", "Main Street, Downtown", True, False, True),
    ("Mall Parking", "City Mall, Uptown", True, True, True),
    ("Airport Lot", "Airport Terminal 1", True, True, False),
)
DEFAULT_SLOT_COUNT = 40


class Command(BaseCommand):
    help = "Seed smart parking lots, slots, and demo vehicle types."

    def handle(self, *args, **options):
        car = VehicleType.objects.get_or_create(name="Car", defaults={"slug": "car", "icon": "car"})[0]
        bike = VehicleType.objects.get_or_create(name="Bike", defaults={"slug": "bike", "icon": "bike"})[0]
        auto = VehicleType.objects.get_or_create(name="Auto Rickshaw", defaults={"slug": "auto", "icon": "auto"})[0]
        bus = VehicleType.objects.get_or_create(name="Bus", defaults={"slug": "bus", "icon": "bus"})[0]
        truck = VehicleType.objects.get_or_create(name="Truck", defaults={"slug": "truck", "icon": "truck"})[0]
        ev_car = VehicleType.objects.get_or_create(name="EV Car", defaults={"slug": "ev-car", "icon": "ev"})[0]
        ev_bike = VehicleType.objects.get_or_create(name="EV Bike", defaults={"slug": "ev-bike", "icon": "ev-bike"})[0]

        facility_ev = Facility.objects.get_or_create(name="EV Charging", defaults={"slug": "ev-charging", "icon": "bolt"})[0]
        facility_cctv = Facility.objects.get_or_create(name="24x7 Security", defaults={"slug": "security", "icon": "shield"})[0]
        facility_covered = Facility.objects.get_or_create(name="Covered", defaults={"slug": "covered", "icon": "umbrella"})[0]

        created_lots = []
        for name, address, allow_car, allow_ev, is_covered in DEFAULT_LOTS:
            lot, created = ParkingLot.objects.get_or_create(name=name, defaults={"address": address, "active": True, "is_covered": is_covered})
            if created:
                created_lots.append(lot.name)
            lot.vehicle_types.add(car, bike, auto, bus, truck)
            if allow_ev:
                lot.vehicle_types.add(ev_car, ev_bike)
            if is_covered:
                lot.facilities.add(facility_covered)
            lot.facilities.add(facility_cctv)
            if allow_ev:
                lot.facilities.add(facility_ev)
            lot.save()

            for idx in range(1, DEFAULT_SLOT_COUNT + 1):
                slot, _ = ParkingSlot.objects.get_or_create(parking_lot=lot, number=idx)
                slot.vehicle_types.add(car, bike)
                if idx % 5 == 0:
                    slot.ev_charger = True
                if name == "Downtown Lot" and idx <= 10:
                    slot.priority = 1
                slot.save()

        demo_bookings = (
            ("KA01AB1234", "Car", "Downtown Lot", 1),
            ("MH12XY9001", "Bike", "Downtown Lot", 3),
        )
        for plate, vehicle_type_name, lot_name, slot_number in demo_bookings:
            vehicle_type = VehicleType.objects.get(name=vehicle_type_name)
            lot = ParkingLot.objects.get(name=lot_name)
            slot = ParkingSlot.objects.get(parking_lot=lot, number=slot_number)
            vehicle, _ = Vehicle.objects.get_or_create(number_plate=plate, defaults={"vehicle_type": vehicle_type})
            existing = Booking.objects.filter(slot=slot, status__in=["reserved", "checked_in"], end_time__isnull=True).exists()
            if not existing:
                Booking.objects.create(
                    booking_id=f"BK-DEM0{slot_number}",
                    vehicle_number=vehicle.number_plate,
                    vehicle_type=vehicle_type,
                    parking_lot=lot,
                    slot=slot,
                    status="reserved",
                    payment_status="pending",
                    start_time=timezone.now(),
                    reservation_expires_at=timezone.now() + timezone.timedelta(minutes=20),
                )
                slot.is_occupied = True
                slot.reserved = True
                slot.save(update_fields=["is_occupied", "reserved"])

        self.stdout.write(self.style.SUCCESS(f"Seeded parking data. Created lots: {created_lots or 'none'}"))
