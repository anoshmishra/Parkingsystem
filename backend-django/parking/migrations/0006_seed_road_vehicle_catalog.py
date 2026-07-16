from django.db import migrations


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
    ("truck", "Truck", "Heavy goods vehicle parking bays.", "truck"),
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


def ensure_vehicle_type(VehicleType, slug, name, description, icon):
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
            name=name,
            slug=slug,
            description=description,
            icon=icon,
            active=True,
        )

    vehicle_type.name = name
    vehicle_type.slug = slug
    vehicle_type.description = description
    vehicle_type.icon = icon
    vehicle_type.active = True
    vehicle_type.save(update_fields=["name", "slug", "description", "icon", "active"])
    return vehicle_type


def ensure_facility(Facility, slug, name, icon):
    facility = Facility.objects.filter(slug=slug).first()
    if facility is None:
        facility = Facility.objects.filter(name=name).first()

    if facility is None:
        return Facility.objects.create(name=name, slug=slug, icon=icon, active=True)

    facility.name = name
    facility.slug = slug
    facility.icon = icon
    facility.active = True
    facility.save(update_fields=["name", "slug", "icon", "active"])
    return facility


def slot_type_slugs(number):
    slugs = list(COMPACT_TYPES)

    if number % 6 != 0:
        slugs.extend(STANDARD_TYPES)

    if number % 5 == 0 or number > 50:
        slugs.extend(LARGE_TYPES)

    return slugs


def seed_road_vehicle_catalog(apps, schema_editor):
    VehicleType = apps.get_model("parking", "VehicleType")
    Facility = apps.get_model("parking", "Facility")
    ParkingLot = apps.get_model("parking", "ParkingLot")
    ParkingSlot = apps.get_model("parking", "ParkingSlot")

    vehicle_types = {
        slug: ensure_vehicle_type(VehicleType, slug, name, description, icon)
        for slug, name, description, icon in VEHICLE_TYPES
    }
    facilities = {
        slug: ensure_facility(Facility, slug, name, icon)
        for slug, name, icon in FACILITIES
    }

    for lot_defaults in LOT_DEFAULTS:
        lot, _ = ParkingLot.objects.get_or_create(name=lot_defaults["name"])
        for field, value in lot_defaults.items():
            if field != "name":
                setattr(lot, field, value)
        lot.capacity = max(lot.capacity or 0, DEFAULT_SLOT_COUNT)
        lot.active = True
        lot.save()

        lot.vehicle_types.add(*vehicle_types.values())
        lot.facilities.add(facilities["security"])
        if lot.is_ev_charging:
            lot.facilities.add(facilities["ev-charging"])
        if lot.is_covered:
            lot.facilities.add(facilities["covered"])
        lot.facilities.add(facilities["large-bays"])

        for number in range(1, DEFAULT_SLOT_COUNT + 1):
            slot, _ = ParkingSlot.objects.get_or_create(parking_lot=lot, number=number)
            floor = 1 if number <= 30 else 2
            zone = "A" if number <= 20 else "B" if number <= 40 else "C"
            slot.floor = floor
            slot.zone = zone
            slot.ev_charger = lot.is_ev_charging and number % 5 == 0
            slot.covered = lot.is_covered
            slot.priority = 1 if lot.recommended and number <= 12 else 2 if number <= 30 else 3
            slot.save(update_fields=["floor", "zone", "ev_charger", "covered", "priority"])
            slot.vehicle_types.add(*(vehicle_types[slug] for slug in slot_type_slugs(number)))


class Migration(migrations.Migration):
    dependencies = [
        ("parking", "0005_align_saas_model_constraints"),
    ]

    operations = [
        migrations.RunPython(seed_road_vehicle_catalog, migrations.RunPython.noop),
    ]
