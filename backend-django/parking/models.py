import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def generate_booking_id():
    return f"BK-{timezone.now().strftime('%y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"


class VehicleType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="car")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Facility(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ParkingLot(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(blank=True)
    opening_hours = models.CharField(max_length=200, default="24/7")
    capacity = models.PositiveIntegerField(default=100)
    security_rating = models.PositiveIntegerField(default=3)
    facilities = models.ManyToManyField(Facility, blank=True)
    vehicle_types = models.ManyToManyField(VehicleType, blank=True)
    price_hint = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    walking_time_minutes = models.PositiveIntegerField(default=5)
    is_ev_charging = models.BooleanField(default=False)
    is_covered = models.BooleanField(default=False)
    is_24x7 = models.BooleanField(default=True)
    map_link = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    recommended = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def supports_vehicle_type(self, vehicle_type):
        if not vehicle_type:
            return False
        return self.vehicle_types.filter(pk=vehicle_type.pk if hasattr(vehicle_type, "pk") else vehicle_type).exists()

    @property
    def available_slot_count(self):
        return self.slots.filter(is_occupied=False, reserved=False, maintenance=False, disabled=False).count()

    def __str__(self):
        return self.name


class ParkingSlot(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name="slots")
    number = models.IntegerField()
    zone = models.CharField(max_length=50, default="A")
    floor = models.PositiveIntegerField(default=1)
    vehicle_types = models.ManyToManyField(VehicleType, blank=True)
    is_occupied = models.BooleanField(default=False)
    reserved = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    disabled = models.BooleanField(default=False)
    ev_charger = models.BooleanField(default=False)
    covered = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("parking_lot", "number")

    def supports_vehicle_type(self, vehicle_type):
        if not vehicle_type:
            return False
        return self.vehicle_types.filter(pk=vehicle_type.pk if hasattr(vehicle_type, "pk") else vehicle_type).exists()

    @property
    def status(self):
        if self.disabled:
            return "Disabled"
        if self.maintenance:
            return "Maintenance"
        if self.is_occupied or self.reserved:
            return "Occupied"
        return "Available"

    def __str__(self):
        return f"{self.parking_lot.name} - Slot {self.number}"


class Vehicle(models.Model):
    number_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, null=True, blank=True, related_name="vehicles")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.number_plate = self.number_plate.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number_plate


class Booking(models.Model):
    STATUS_CHOICES = (
        ("reserved", "Reserved"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    )
    PAYMENT_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("refunded", "Refunded"),
    )

    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, related_name="bookings")
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.PROTECT, related_name="bookings")
    slot = models.ForeignKey(ParkingSlot, on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="reserved")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = generate_booking_id()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in {"reserved", "checked_in"} and self.end_time is None

    def __str__(self):
        return f"{self.booking_id} - {self.vehicle_number}"


class BookingHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.booking.booking_id} - {self.action}"
