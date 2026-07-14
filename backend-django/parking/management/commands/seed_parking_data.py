from django.core.management.base import BaseCommand
from parking.models import ParkingLot, Slot


class Command(BaseCommand):
    help = "Ensure each parking lot has 50 slots and seed the default lots if none exist."

    def handle(self, *args, **options):
        created_lots = []
        lot_names = ["Downtown Lot", "Mall Parking", "Airport Lot"]
        for name in lot_names:
            lot, created = ParkingLot.objects.get_or_create(name=name)
            if created:
                created_lots.append(lot.name)

        for lot in ParkingLot.objects.all():
            existing = Slot.objects.filter(lot=lot).count()
            target = 50
            for idx in range(existing + 1, target + 1):
                Slot.objects.get_or_create(lot=lot, number=idx)

        self.stdout.write(self.style.SUCCESS(f"Seeded parking lots and slots. Created lots: {created_lots or 'none'}"))
