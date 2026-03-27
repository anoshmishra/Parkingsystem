from django.contrib import admin

from .models import Booking, ParkingLot, Slot, Vehicle

admin.site.register(ParkingLot)
admin.site.register(Slot)
admin.site.register(Vehicle)
admin.site.register(Booking)
