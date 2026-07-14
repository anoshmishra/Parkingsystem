from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Booking, ParkingLot, ParkingSlot, VehicleType
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    ParkingLotSerializer,
    ParkingSlotSerializer,
    VehicleTypeSerializer,
)
from .services import BookingService


@api_view(["GET"])
def api_root(request):
    return Response(
        {
            "message": "Smart parking API is running",
            "endpoints": {
                "vehicle_types": "/api/vehicle-types/",
                "lots": "/api/lots/",
                "available_slots": "/api/lots/<lot_id>/slots/available/",
                "bookings": "/api/bookings/",
                "checkout": "/api/bookings/<booking_id>/checkout/",
            },
        }
    )


@api_view(["GET"])
def list_vehicle_types(request):
    BookingService.expire_reservations()
    vehicle_types = VehicleType.objects.filter(active=True).order_by("name")
    serializer = VehicleTypeSerializer(vehicle_types, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def list_lots(request):
    BookingService.expire_reservations()
    vehicle_type_filter = request.GET.get("vehicle_type", "").strip()
    lots = ParkingLot.objects.filter(active=True).prefetch_related("vehicle_types", "facilities").order_by("name")

    if vehicle_type_filter:
        vehicle_type = VehicleType.objects.filter(Q(pk=vehicle_type_filter) | Q(slug=vehicle_type_filter)).first()
        if vehicle_type:
            lots = lots.filter(vehicle_types=vehicle_type)
        else:
            lots = lots.none()

    serializer = ParkingLotSerializer(lots, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_available_slots(request, lot_id):
    BookingService.expire_reservations()
    lot = get_object_or_404(ParkingLot, pk=lot_id, active=True)
    vehicle_type_filter = request.GET.get("vehicle_type", "").strip()
    slot_filter = request.GET.get("filter", "available")

    if slot_filter not in ("available", "occupied", "all"):
        return Response({"success": False, "message": "Unsupported slot filter"}, status=status.HTTP_400_BAD_REQUEST)

    active_bookings = Booking.objects.filter(
        slot_id=OuterRef("pk"),
        status__in=["reserved", "checked_in"],
        end_time__isnull=True,
    )
    slots = (
        ParkingSlot.objects.filter(parking_lot=lot)
        .annotate(has_active_booking=Exists(active_bookings))
        .select_related("parking_lot")
        .prefetch_related("vehicle_types")
        .order_by("floor", "zone", "number")
    )

    if vehicle_type_filter:
        vehicle_type = VehicleType.objects.filter(Q(pk=vehicle_type_filter) | Q(slug=vehicle_type_filter)).first()
        if vehicle_type:
            slots = slots.filter(vehicle_types=vehicle_type)
        else:
            slots = slots.none()

    if slot_filter == "available":
        slots = slots.filter(
            is_occupied=False,
            reserved=False,
            maintenance=False,
            disabled=False,
            has_active_booking=False,
        )
    elif slot_filter == "occupied":
        slots = slots.filter(
            Q(is_occupied=True)
            | Q(reserved=True)
            | Q(maintenance=True)
            | Q(disabled=True)
            | Q(has_active_booking=True)
        )

    serializer = ParkingSlotSerializer(slots, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST"])
def bookings(request):
    BookingService.expire_reservations()
    if request.method == "GET":
        search = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status", "").strip()
        bookings_qs = Booking.objects.select_related("vehicle_type", "parking_lot", "slot").order_by("-created_at")
        if search:
            bookings_qs = bookings_qs.filter(
                Q(vehicle_number__icontains=search)
                | Q(booking_id__icontains=search)
                | Q(parking_lot__name__icontains=search)
                | Q(vehicle_type__name__icontains=search)
            )
        if status_filter:
            bookings_qs = bookings_qs.filter(status=status_filter)
        serializer = BookingSerializer(bookings_qs, many=True)
        return Response(serializer.data)

    serializer = BookingCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "message": "Validation failed", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        booking = serializer.save()
    except ValidationError as exc:
        detail = exc.detail
        message = detail.get("detail") if isinstance(detail, dict) else detail
        if isinstance(message, list):
            message = message[0]
        message = str(message or "Validation failed")
        return Response(
            {"success": False, "message": message, "detail": message, "errors": detail},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


@api_view(["POST", "PATCH"])
def checkout_booking(request, booking_id):
    BookingService.expire_reservations()
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update().select_related("slot"), pk=booking_id)
        if booking.status == "checked_out":
            return Response({"success": True, "message": "Booking already checked out"})

        booking.status = "checked_out"
        booking.payment_status = "paid"
        booking.end_time = booking.end_time or timezone.now()
        booking.save(update_fields=["status", "payment_status", "end_time"])
        booking.slot.is_occupied = False
        booking.slot.reserved = False
        booking.slot.save(update_fields=["is_occupied", "reserved"])
    return Response({"success": True, "message": "Checked out successfully"})
