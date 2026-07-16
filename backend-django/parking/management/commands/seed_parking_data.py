from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from parking.models import Booking, Facility, ParkingLot, ParkingSlot, Vehicle, VehicleType


DEFAULT_SLOT_COUNT = 60

VEHICLE_TYPES = (
    ("bicycle", "Bicycle", "Cycle parking for road-going bicycles.", "bike"),
    ("motorcycle", "Motorcycle", "Two-wheeler parking for motorcycles.", "bike"),
    ("scooter", "Scooter", "Compact parking for scooters and mopeds.", "scooter"),
    ("ev-two-wheeler", "EV Two-Wheeler", "Charging-aware parking for electric scooters and motorcycles.", "ev-bike"),
    ("car", "Car", "Standard private car parking.", "car"),
    ("ev-car", "EV Car", "Charging-aware parking for electric cars.", "ev"),
    ("suv", "SUV", "Larger bays for SUVs and crossovers.", "car"),
    ("van", "Van", "Parking for passenger and goods vans.", "van"),
    ("auto-rickshaw", "Auto Rickshaw", "Three-wheeler passenger vehicle parking.", "auto"),
    ("e-rickshaw", "E-Rickshaw", "Electric three-wheeler parking.", "ev"),
    ("pickup-truck", "Pickup Truck", "Light commercial pickup parking.", "truck"),
    ("mini-truck", "Mini Truck", "Small goods vehicle parking.", "truck"),
    ("truck", "Truck", "Heavy goods vehicle parking.", "truck"),
    ("bus", "Bus", "Bus and coach parking bays.", "bus"),
    ("tractor", "Tractor", "Agricultural and utility tractor parking.", "tractor"),
    ("emergency-vehicle", "Emergency Vehicle", "Ambulance and response vehicle parking.", "ambulance"),
)

VEHICLE_ALIASES = {
    "motorcycle": (("slug", "bike"), ("name", "Bike")),
    "auto-rickshaw": (("slug", "auto"),),
    "ev-two-wheeler": (("slug", "ev-bike"), ("name", "EV Bike")),
}

FACILITIES = (
    ("ev-charging", "EV Charging", "bolt"),
    ("security", "24x7 Security", "shield"),
    ("covered", "Covered", "umbrella"),
    ("large-bays", "Large Bays", "truck"),
)

LOT_DEFAULTS = (
    {
        "name": "Downtown Lot",
        "address": "Main Street, Downtown",
        "description": "Central city parking with fast access to offices and retail.",
        "price_hint": "80.00",
        "distance_km": "0.30",
        "walking_time_minutes": 4,
        "security_rating": 4,
        "is_ev_charging": True,
        "is_covered": True,
        "is_24x7": True,
        "recommended": True,
    },
    {
        "name": "Mall Parking",
        "address": "City Mall, Uptown",
        "description": "Covered shopping district parking with EV support.",
        "price_hint": "60.00",
        "distance_km": "0.60",
        "walking_time_minutes": 6,
        "security_rating": 5,
        "is_ev_charging": True,
        "is_covered": True,
        "is_24x7": True,
        "recommended": False,
    },
    {
        "name": "Airport Lot",
        "address": "Airport Terminal 1",
        "description": "High-capacity long-stay lot with large vehicle bays.",
        "price_hint": "120.00",
        "distance_km": "1.20",
        "walking_time_minutes": 10,
        "security_rating": 5,
        "is_ev_charging": False,
        "is_covered": False,
        "is_24x7": True,
        "recommended": False,
    },
)

COMPACT_TYPES = ("bicycle", "motorcycle", "scooter", "ev-two-wheeler")
STANDARD_TYPES = (
    "car",
    "ev-car",
    "suv",
    "van",
    "auto-rickshaw",
    "e-rickshaw",
)
LARGE_TYPES = (
    "pickup-truck",
    "mini-truck",
    "truck",
    "bus",
    "tractor",
    "emergency-vehicle",
)


def slot_type_slugs(number):
    slugs = list(COMPACT_TYPES)
    if number % 6 != 0:
        slugs.extend(STANDARD_TYPES)
    if number % 5 == 0 or number > 50:
        slugs.extend(LARGE_TYPES)
    return slugs


def ensure_vehicle_type(slug, name, description, icon):
    vehicle_type = VehicleType.objects.filter(slug=slug).first()
    if vehicle_type is None:
        vehicle_type = VehicleType.objects.filter(name=name).first()
    if vehicle_type is None:
        for field, value in VEHICLE_ALIASES.get(slug, ()):
            vehicle_type = VehicleType.objects.filter(**{field: value}).first()
            if vehicle_type is not None:
                break

    if vehicle_type is None:
        return VehicleType.objects.create(
            slug=slug,
            name=name,
            description=description,
            icon=icon,
            active=True,
        )

    vehicle_type.slug = slug
    vehicle_type.name = name
    vehicle_type.description = description
    vehicle_type.icon = icon
    vehicle_type.active = True
    vehicle_type.save(update_fields=["slug", "name", "description", "icon", "active"])
    return vehicle_type


def ensure_facility(slug, name, icon):
    facility = Facility.objects.filter(slug=slug).first()
    if facility is None:
        facility = Facility.objects.filter(name=name).first()

    if facility is None:
        return Facility.objects.create(slug=slug, name=name, icon=icon, active=True)

    facility.slug = slug
    facility.name = name
    facility.icon = icon
    facility.active = True
    facility.save(update_fields=["slug", "name", "icon", "active"])
    return facility


class Command(BaseCommand):
    help = "Seed smart parking lots, slots, and demo vehicle types."

    def handle(self, *args, **options):
        vehicle_types = {}
        for slug, name, description, icon in VEHICLE_TYPES:
            vehicle_types[slug] = ensure_vehicle_type(slug, name, description, icon)

        facilities = {}
        for slug, name, icon in FACILITIES:
            facilities[slug] = ensure_facility(slug, name, icon)

        created_lots = []
        for lot_defaults in LOT_DEFAULTS:
            lot, created = ParkingLot.objects.get_or_create(name=lot_defaults["name"])
            if created:
                created_lots.append(lot.name)

            for field, value in lot_defaults.items():
                if field != "name":
                    setattr(lot, field, value)
            lot.capacity = max(lot.capacity or 0, DEFAULT_SLOT_COUNT)
            lot.active = True
            lot.save()
            lot.vehicle_types.add(*vehicle_types.values())
            lot.facilities.add(facilities["security"], facilities["large-bays"])
            if lot.is_ev_charging:
                lot.facilities.add(facilities["ev-charging"])
            if lot.is_covered:
                lot.facilities.add(facilities["covered"])

            for idx in range(1, DEFAULT_SLOT_COUNT + 1):
                slot, _ = ParkingSlot.objects.get_or_create(parking_lot=lot, number=idx)
                slot.floor = 1 if idx <= 30 else 2
                slot.zone = "A" if idx <= 20 else "B" if idx <= 40 else "C"
                slot.ev_charger = lot.is_ev_charging and idx % 5 == 0
                slot.covered = lot.is_covered
                slot.priority = 1 if lot.recommended and idx <= 12 else 2 if idx <= 30 else 3
                slot.save()
                slot.vehicle_types.add(*(vehicle_types[slug] for slug in slot_type_slugs(idx)))

        demo_bookings = (
            ("KA01AB1234", "Car", "Downtown Lot", 1),
            ("MH12XY9001", "Motorcycle", "Downtown Lot", 3),
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
                    reservation_expires_at=timezone.now() + timedelta(minutes=20),
                )
                slot.is_occupied = True
                slot.reserved = True
                slot.save(update_fields=["is_occupied", "reserved"])

        self.stdout.write(self.style.SUCCESS(f"Seeded parking data. Created lots: {created_lots or 'none'}"))
