from rest_framework import serializers
from .models import ParkingLot, Slot, Vehicle, Booking

class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        fields = '__all__'

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = '__all__'

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