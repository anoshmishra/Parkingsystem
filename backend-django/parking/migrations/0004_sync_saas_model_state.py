# Generated during Phase 1 RC validation.

import django.utils.timezone
from django.db import migrations, models


def backfill_vehicle_type_relationships(apps, schema_editor):
    VehicleType = apps.get_model("parking", "VehicleType")
    ParkingLot = apps.get_model("parking", "ParkingLot")
    ParkingSlot = apps.get_model("parking", "ParkingSlot")
    Vehicle = apps.get_model("parking", "Vehicle")
    Booking = apps.get_model("parking", "Booking")

    car = VehicleType.objects.filter(slug="car").first() or VehicleType.objects.filter(name="Car").first()
    if car is None:
        car = VehicleType.objects.create(name="Car", slug="car", icon="car", active=True)

    for lot in ParkingLot.objects.all():
        lot.vehicle_types.add(car)

    for slot in ParkingSlot.objects.all():
        slot.vehicle_types.add(car)

    Vehicle.objects.filter(vehicle_type__isnull=True).update(vehicle_type=car)

    for booking in Booking.objects.filter(vehicle_type__isnull=True):
        vehicle = Vehicle.objects.filter(number_plate=booking.vehicle_number).first()
        booking.vehicle_type = vehicle.vehicle_type if vehicle and vehicle.vehicle_type_id else car
        booking.save(update_fields=["vehicle_type"])


class Migration(migrations.Migration):

    dependencies = [
        ("parking", "0003_upgrade_saas_parking_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingslot",
            name="covered",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="disabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="ev_charger",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="floor",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="maintenance",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="priority",
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="reserved",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="parkingslot",
            name="zone",
            field=models.CharField(default="A", max_length=50),
        ),
        migrations.RunPython(backfill_vehicle_type_relationships, migrations.RunPython.noop),
    ]
