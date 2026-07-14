import datetime

from django.db import migrations


DEFAULT_LOTS = ("Downtown Lot", "Mall Parking", "Airport Lot")
DEFAULT_SLOT_COUNT = 50


def ensure_slot(Slot, lot, number):
    slot = Slot.objects.filter(lot=lot, number=number).first()
    if slot is None:
        slot = Slot.objects.create(lot=lot, number=number)
    return slot


def seed_default_parking_data(apps, schema_editor):
    ParkingLot = apps.get_model("parking", "ParkingLot")
    Slot = apps.get_model("parking", "Slot")
    Vehicle = apps.get_model("parking", "Vehicle")
    Booking = apps.get_model("parking", "Booking")

    lots = {}
    for lot_name in DEFAULT_LOTS:
        lot, _ = ParkingLot.objects.get_or_create(name=lot_name)
        lots[lot_name] = lot

        for number in range(1, DEFAULT_SLOT_COUNT + 1):
            ensure_slot(Slot, lot, number)

    demo_bookings = (
        (
            "KA01AB1234",
            "Downtown Lot",
            1,
            datetime.datetime(2026, 3, 26, 8, 0, tzinfo=datetime.timezone.utc),
        ),
        (
            "MH12XY9001",
            "Downtown Lot",
            3,
            datetime.datetime(2026, 3, 26, 8, 30, tzinfo=datetime.timezone.utc),
        ),
    )

    for plate, lot_name, slot_number, start_time in demo_bookings:
        vehicle, _ = Vehicle.objects.get_or_create(number_plate=plate)
        slot = ensure_slot(Slot, lots[lot_name], slot_number)
        has_active_booking = Booking.objects.filter(
            slot=slot,
            end_time__isnull=True,
        ).exists()
        if not has_active_booking:
            Booking.objects.create(vehicle=vehicle, slot=slot, start_time=start_time)
        if not slot.is_occupied:
            slot.is_occupied = True
            slot.save(update_fields=["is_occupied"])


class Migration(migrations.Migration):
    dependencies = [
        ("parking", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_parking_data, migrations.RunPython.noop),
    ]
