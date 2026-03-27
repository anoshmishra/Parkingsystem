from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import ParkingLot, Slot, Vehicle, Booking
from .serializers import ParkingLotSerializer, SlotSerializer, BookingSerializer, VehicleSerializer

@api_view(['GET'])
def list_lots(request):
    lots = ParkingLot.Project.all() if hasattr(ParkingLot, 'Project') else ParkingLot.objects.all()
    serializer = ParkingLotSerializer(lots, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_available_slots(request, lot_id):
    slots = Slot.objects.filter(lot_id=lot_id, is_occupied=False)
    serializer = SlotSerializer(slots, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
def bookings(request):
    if request.method == 'GET':
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        data = request.data
        serializer = BookingSerializer(data=data)
        
        if serializer.is_valid():
            # Save the booking
            booking = serializer.save()
            
            # CRITICAL: Mark the slot as occupied in the database
            slot = booking.slot
            slot.is_occupied = True
            slot.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # This will return the EXACT reason for the 400 error
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def checkout_booking(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.end_time = timezone.now()
        booking.save()

        # Mark slot as free again
        slot = booking.slot
        slot.is_occupied = False
        slot.save()

        return Response({"message": "Checked out successfully"})
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)