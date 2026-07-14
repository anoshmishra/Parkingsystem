from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ParkingLot, Slot, Vehicle, Booking
from .serializers import (
    ParkingLotSerializer,
    SlotSerializer,
    VehicleSerializer,
    BookingSerializer,
)


def _slot_queryset(lot_id):
    active_bookings = Booking.objects.filter(slot_id=OuterRef("pk"), end_time__isnull=True)
    return Slot.objects.filter(lot_id=lot_id).annotate(
        has_active_booking=Exists(active_bookings)
    ).order_by("number")


def _serializer_error_message(errors):
    messages = []
    for field, details in errors.items():
        if isinstance(details, (list, tuple)):
            detail = " ".join(str(item) for item in details)
        else:
            detail = str(details)
        messages.append(f"{field}: {detail}")
    return "; ".join(messages) if messages else "Validation error"


def _sync_slot_occupancy(slot):
    is_occupied = Booking.objects.filter(slot=slot, end_time__isnull=True).exists()
    if slot.is_occupied != is_occupied:
        slot.is_occupied = is_occupied
        slot.save(update_fields=["is_occupied"])
    return is_occupied


def _booking_data_with_vehicle(request):
    data = request.data.copy()
    number_plate = str(
        data.get("vehicle_number") or data.get("number_plate") or ""
    ).strip()

    if not number_plate:
        return data, None

    if len(number_plate) > Vehicle._meta.get_field("number_plate").max_length:
        return None, Response(
            {"success": False, "message": "Vehicle number must be 20 characters or fewer"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    normalized_plate = number_plate.upper()
    vehicle = Vehicle.objects.filter(number_plate__iexact=normalized_plate).first()
    if vehicle is None:
        vehicle = Vehicle.objects.create(number_plate=normalized_plate)

    data["vehicle"] = vehicle.pk
    return data, None


@api_view(['GET'])
def api_root(request):
    return Response({
        "message": "Parking API is running",
        "endpoints": {
            "lots": "/api/lots/",
            "vehicles": "/api/vehicles/",
            "available_slots": "/api/lots/<lot_id>/slots/available/",
            "bookings": "/api/bookings/",
            "checkout": "/api/bookings/<booking_id>/checkout/",
        },
    })


@api_view(['GET'])
def list_lots(request):
    lots = ParkingLot.objects.all()
    serializer = ParkingLotSerializer(lots, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def list_vehicles(request):
    vehicles = Vehicle.objects.all().order_by("number_plate")
    serializer = VehicleSerializer(vehicles, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_available_slots(request, lot_id):
    slot_filter = request.GET.get('filter', 'available')
    if slot_filter not in ('available', 'occupied', 'all'):
        return Response(
            {"success": False, "message": "Unsupported slot filter"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slots = _slot_queryset(lot_id)
    if slot_filter == 'available':
        slots = slots.filter(has_active_booking=False)
    elif slot_filter == 'occupied':
        slots = slots.filter(has_active_booking=True)

    serializer = SlotSerializer(slots, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def bookings(request):
    if request.method == 'GET':
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        booking_data, error_response = _booking_data_with_vehicle(request)
        if error_response is not None:
            return error_response

        serializer = BookingSerializer(data=booking_data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": _serializer_error_message(serializer.errors)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            slot = Slot.objects.select_for_update().get(
                pk=serializer.validated_data["slot"].pk
            )
            has_active_booking = Booking.objects.select_for_update().filter(
                slot=slot,
                end_time__isnull=True,
            ).exists()

            if has_active_booking:
                _sync_slot_occupancy(slot)
                return Response(
                    {"success": False, "message": "Slot already booked"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            booking = serializer.save(slot=slot)
            slot.is_occupied = True
            slot.save(update_fields=["is_occupied"])
            booking.slot = slot

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'PATCH'])
def checkout_booking(request, booking_id):
    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().select_related("slot").get(
                id=booking_id
            )
            if booking.end_time is not None:
                _sync_slot_occupancy(booking.slot)
                return Response({"success": True, "message": "Booking already checked out"})

            booking.end_time = timezone.now()
            booking.save(update_fields=["end_time"])
            _sync_slot_occupancy(booking.slot)

        return Response({"success": True, "message": "Checked out successfully"})
    except Booking.DoesNotExist:
        return Response(
            {"success": False, "message": "Booking not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
