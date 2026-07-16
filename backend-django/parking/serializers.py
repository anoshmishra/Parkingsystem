from rest_framework import serializers

from .models import Booking, BookingHistory, Facility, ParkingLot, ParkingSlot, Vehicle, VehicleType
from .services import BookingService


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = ["id", "name", "slug", "description", "icon", "active"]


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "name", "slug", "icon", "active"]


class ParkingLotSerializer(serializers.ModelSerializer):
    vehicle_types = VehicleTypeSerializer(many=True, read_only=True)
    facilities = FacilitySerializer(many=True, read_only=True)
    available_slot_count = serializers.SerializerMethodField()

    def get_available_slot_count(self, obj):
        slots = obj.slots.filter(is_occupied=False, reserved=False, maintenance=False, disabled=False)
        vehicle_type = self.context.get("vehicle_type")
        if vehicle_type:
            slots = slots.filter(vehicle_types=vehicle_type)

        active_booking_slot_ids = Booking.objects.filter(
            slot__parking_lot=obj,
            status__in=["reserved", "checked_in"],
            end_time__isnull=True,
        ).values("slot_id")
        return slots.exclude(pk__in=active_booking_slot_ids).count()

    class Meta:
        model = ParkingLot
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "description",
            "opening_hours",
            "capacity",
            "security_rating",
            "price_hint",
            "distance_km",
            "walking_time_minutes",
            "is_ev_charging",
            "is_covered",
            "is_24x7",
            "map_link",
            "image_url",
            "recommended",
            "active",
            "vehicle_types",
            "facilities",
            "available_slot_count",
        ]


class ParkingSlotSerializer(serializers.ModelSerializer):
    parking_lot = serializers.PrimaryKeyRelatedField(read_only=True)
    vehicle_types = VehicleTypeSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = ParkingSlot
        fields = [
            "id",
            "parking_lot",
            "number",
            "zone",
            "floor",
            "vehicle_types",
            "is_occupied",
            "reserved",
            "maintenance",
            "disabled",
            "ev_charger",
            "covered",
            "priority",
            "status",
        ]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "number_plate", "vehicle_type"]


class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingHistory
        fields = ["id", "action", "details", "created_at"]


class BookingSerializer(serializers.ModelSerializer):
    vehicle_type = VehicleTypeSerializer(read_only=True)
    parking_lot = ParkingLotSerializer(read_only=True)
    slot = ParkingSlotSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_id",
            "vehicle_number",
            "vehicle_type",
            "parking_lot",
            "slot",
            "status",
            "payment_status",
            "start_time",
            "end_time",
            "duration_minutes",
            "reservation_expires_at",
            "created_at",
            "updated_at",
        ]


class BookingCreateSerializer(serializers.Serializer):
    vehicle_number = serializers.CharField(max_length=20)
    vehicle_type = serializers.PrimaryKeyRelatedField(queryset=VehicleType.objects.all())
    parking_lot = serializers.PrimaryKeyRelatedField(queryset=ParkingLot.objects.all())
    slot = serializers.PrimaryKeyRelatedField(queryset=ParkingSlot.objects.all())
    reservation_minutes = serializers.IntegerField(required=False, default=15, min_value=5, max_value=240)

    def create(self, validated_data):
        try:
            return BookingService.create_booking(
                vehicle_number=validated_data["vehicle_number"],
                vehicle_type=validated_data["vehicle_type"],
                parking_lot=validated_data["parking_lot"],
                slot=validated_data["slot"],
                reservation_minutes=validated_data.get("reservation_minutes", 15),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
