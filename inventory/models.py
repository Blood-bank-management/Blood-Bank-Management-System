from django.db import models


class BloodInventory(models.Model):
    blood_group = models.CharField(max_length=3)
    quantity = models.PositiveIntegerField(default=0)
    collection_date = models.DateField()
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.blood_group} - {self.quantity} units"