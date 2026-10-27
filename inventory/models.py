from django.db import models
from django.core.exceptions import ValidationError


class BloodInventory(models.Model):
    blood_group = models.CharField(max_length=3)
    quantity = models.PositiveIntegerField(default=0)
    collection_date = models.DateField()
    expiry_date = models.DateField()

    def clean(self):
        if self.expiry_date < self.collection_date:
            raise ValidationError(
                "Expiry date cannot be before collection date."
            )

    def __str__(self):
        return f"{self.blood_group} - {self.quantity} units"