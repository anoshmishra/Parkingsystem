# Generated during Phase 1 RC validation.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("parking", "0004_sync_saas_model_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="booking_id",
            field=models.CharField(editable=False, max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name="booking",
            name="duration_minutes",
            field=models.PositiveIntegerField(default=60),
        ),
        migrations.AlterField(
            model_name="booking",
            name="parking_lot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bookings",
                to="parking.parkinglot",
            ),
        ),
        migrations.AlterField(
            model_name="booking",
            name="payment_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("paid", "Paid"), ("refunded", "Refunded")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="booking",
            name="slot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bookings",
                to="parking.parkingslot",
            ),
        ),
        migrations.AlterField(
            model_name="booking",
            name="status",
            field=models.CharField(
                choices=[
                    ("reserved", "Reserved"),
                    ("checked_in", "Checked In"),
                    ("checked_out", "Checked Out"),
                    ("cancelled", "Cancelled"),
                    ("expired", "Expired"),
                ],
                default="reserved",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="booking",
            name="vehicle_number",
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name="booking",
            name="vehicle_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="bookings",
                to="parking.vehicletype",
            ),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="active",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="capacity",
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="distance_km",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="is_24x7",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="is_covered",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="is_ev_charging",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="opening_hours",
            field=models.CharField(default="24/7", max_length=200),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="price_hint",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="recommended",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="security_rating",
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.AlterField(
            model_name="parkinglot",
            name="walking_time_minutes",
            field=models.PositiveIntegerField(default=5),
        ),
        migrations.AlterField(
            model_name="parkingslot",
            name="parking_lot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="slots",
                to="parking.parkinglot",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="parkingslot",
            unique_together={("parking_lot", "number")},
        ),
    ]
