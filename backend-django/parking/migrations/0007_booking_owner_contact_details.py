from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("parking", "0006_seed_road_vehicle_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="owner_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="booking",
            name="owner_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="booking",
            name="owner_phone",
            field=models.CharField(blank=True, default="", max_length=25),
        ),
    ]
