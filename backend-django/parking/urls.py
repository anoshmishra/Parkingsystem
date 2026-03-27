from django.urls import path

from .views import bookings, checkout_booking, get_available_slots, list_lots

urlpatterns = [
    path("lots/", list_lots, name="list-lots"),
    path("lots/<int:lot_id>/slots/available/", get_available_slots, name="available-slots"),
    path("bookings/", bookings, name="bookings"),
    path("bookings/<int:booking_id>/checkout/", checkout_booking, name="checkout-booking"),
]
