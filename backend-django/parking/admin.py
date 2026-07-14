from django.contrib import admin
from django.utils import timezone

from .models import Booking, ParkingLot, Slot, Vehicle

admin.site.site_header = "Parking Control Center"
admin.site.site_title = "Parking Admin"
admin.site.index_title = "Operations Dashboard"


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ("name", "slot_count", "active_booking_count")
    search_fields = ("name",)

    def slot_count(self, obj):
        return obj.slot_set.count()

    def active_booking_count(self, obj):
        return obj.slot_set.filter(booking__end_time__isnull=True).count()

    slot_count.short_description = "Slots"
    active_booking_count.short_description = "Active bookings"


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("lot", "number", "status", "current_vehicle", "booked_since")
    list_filter = ("lot", "is_occupied")
    search_fields = ("number", "lot__name")
    actions = ("mark_as_available", "mark_as_occupied")

    def status(self, obj):
        return "Occupied" if obj.is_occupied else "Available"

    def current_vehicle(self, obj):
        booking = obj.booking_set.filter(end_time__isnull=True).select_related("vehicle").first()
        return booking.vehicle.number_plate if booking else "-"

    def booked_since(self, obj):
        booking = obj.booking_set.filter(end_time__isnull=True).select_related("vehicle").first()
        return booking.start_time.strftime("%Y-%m-%d %H:%M") if booking else "-"

    @admin.action(description="Mark selected slots as available")
    def mark_as_available(self, request, queryset):
        queryset.update(is_occupied=False)

    @admin.action(description="Mark selected slots as occupied")
    def mark_as_occupied(self, request, queryset):
        queryset.update(is_occupied=True)

    status.short_description = "Status"
    current_vehicle.short_description = "Current vehicle"
    booked_since.short_description = "Booked since"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("number_plate", "booking_count", "last_booking")
    search_fields = ("number_plate",)

    def booking_count(self, obj):
        return obj.booking_set.count()

    def last_booking(self, obj):
        booking = obj.booking_set.order_by("-start_time").first()
        return booking.start_time.strftime("%Y-%m-%d %H:%M") if booking else "-"

    booking_count.short_description = "Bookings"
    last_booking.short_description = "Last booked"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle_plate", "slot_display", "start_time", "end_time", "is_active")
    list_filter = ("slot__lot", "start_time", "end_time")
    search_fields = ("vehicle__number_plate", "slot__lot__name", "slot__number")
    actions = ("checkout_selected",)

    def vehicle_plate(self, obj):
        return obj.vehicle.number_plate

    def slot_display(self, obj):
        return f"{obj.slot.lot.name} / Slot {obj.slot.number}"

    def is_active(self, obj):
        return obj.end_time is None

    @admin.action(description="Check out selected bookings")
    def checkout_selected(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(end_time__isnull=True).update(end_time=now)
        self.message_user(request, f"Checked out {updated} active booking(s).")

    vehicle_plate.short_description = "Vehicle"
    slot_display.short_description = "Slot"
    is_active.short_description = "Active"
