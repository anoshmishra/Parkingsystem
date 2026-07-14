from rest_framework import serializers
from .models import ParkingLot, Slot, Vehicle, Booking


class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        fields = '__all__'


class SlotSerializer(serializers.ModelSerializer):
    is_occupied = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = '__all__'

    def get_is_occupied(self, instance):
        active_booking = getattr(instance, 'has_active_booking', None)
        if active_booking is not None:
            return active_booking
        return instance.is_occupied


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'vehicle', 'slot', 'start_time', 'end_time']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['vehicle'] = VehicleSerializer(instance.vehicle).data
        representation['slot'] = SlotSerializer(instance.slot).data
        return representation
