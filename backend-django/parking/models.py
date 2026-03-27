from django.db import models


class ParkingLot(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Slot(models.Model):
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    number = models.IntegerField()
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.lot.name} - Slot {self.number}"


class Vehicle(models.Model):
    number_plate = models.CharField(max_length=20)

    def __str__(self):
        return self.number_plate


class Booking(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle.number_plate} @ {self.slot}"
