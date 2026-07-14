from django.core.management.base import BaseCommand
from django.utils import timezone
from parking.models import ParkingLot, Slot
from parking.models import Booking, Vehicle


DEFAULT_LOTS = ("Downtown Lot", "Mall Parking", "Airport Lot")
DEFAULT_SLOT_COUNT = 50


def ensure_slot(lot, number):
    slot = Slot.objects.filter(lot=lot, number=number).first()
    if slot is None:
        slot = Slot.objects.create(lot=lot, number=number)
    return slot


class Command(BaseCommand):
    help = "Seed default parking lots, slots, vehicles, and active demo bookings."

    def handle(self, *args, **options):
        created_lots = []
        lots = {}

        for name in DEFAULT_LOTS:
            lot, created = ParkingLot.objects.get_or_create(name=name)
            lots[name] = lot
            if created:
                created_lots.append(lot.name)

        for lot in ParkingLot.objects.all():
            for idx in range(1, DEFAULT_SLOT_COUNT + 1):
                ensure_slot(lot, idx)

        demo_bookings = (
            ("KA01AB1234", "Downtown Lot", 1),
            ("MH12XY9001", "Downtown Lot", 3),
        )

        for plate, lot_name, slot_number in demo_bookings:
            vehicle, _ = Vehicle.objects.get_or_create(number_plate=plate)
            slot = ensure_slot(lots[lot_name], slot_number)
            has_active_booking = Booking.objects.filter(
                slot=slot,
                end_time__isnull=True,
            ).exists()
            if not has_active_booking:
                Booking.objects.create(
                    vehicle=vehicle,
                    slot=slot,
                    start_time=timezone.now(),
                )
            if not slot.is_occupied:
                slot.is_occupied = True
                slot.save(update_fields=["is_occupied"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded parking data. Created lots: {created_lots or 'none'}"
            )
        )
