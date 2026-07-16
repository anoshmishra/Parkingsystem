from django.contrib import admin
from django.db import transaction
from django.utils import timezone

from .models import Booking, BookingHistory, Facility, ParkingLot, ParkingSlot, Vehicle, VehicleType

admin.site.site_header = "Parking Control Center"
admin.site.site_title = "Parking Admin"
admin.site.index_title = "Operations Dashboard"


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active")
    search_fields = ("name", "slug")


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active")
    search_fields = ("name",)


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "active", "available_slot_count")
    search_fields = ("name", "address")
    filter_horizontal = ("facilities", "vehicle_types")


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ("parking_lot", "number", "zone", "floor", "status", "priority")
    list_filter = ("parking_lot", "disabled", "maintenance", "is_occupied")
    list_select_related = ("parking_lot",)
    search_fields = ("parking_lot__name", "number", "zone")
    filter_horizontal = ("vehicle_types",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("number_plate", "vehicle_type", "created_at")
    list_select_related = ("vehicle_type",)
    search_fields = ("number_plate",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_id", "owner_name", "owner_email", "vehicle_number", "parking_lot", "slot", "status", "payment_status", "reservation_expires_at")
    list_filter = ("status", "payment_status", "parking_lot")
    list_select_related = ("parking_lot", "slot", "vehicle_type")
    search_fields = ("booking_id", "owner_name", "owner_email", "owner_phone", "vehicle_number", "parking_lot__name")

    def checkout_selected(self, request, queryset):
        now = timezone.now()
        bookings = queryset.filter(status__in=["reserved", "checked_in"]).select_related("slot")
        updated = 0
        with transaction.atomic():
            for booking in bookings.select_for_update():
                booking.status = "checked_out"
                booking.payment_status = "paid"
                booking.end_time = booking.end_time or now
                booking.save(update_fields=["status", "payment_status", "end_time"])
                booking.slot.is_occupied = False
                booking.slot.reserved = False
                booking.slot.save(update_fields=["is_occupied", "reserved"])
                updated += 1
        self.message_user(request, f"Checked out {updated} booking(s).")

    actions = ("checkout_selected",)


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ("booking", "action", "created_at")
    list_select_related = ("booking",)
    search_fields = ("booking__booking_id", "action")
