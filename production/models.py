from __future__ import annotations

from django.db import models
from django.utils import timezone


class Challan(models.Model):
    class Direction(models.TextChoices):
        INBOUND = "IN", "IN"
        OUTBOUND = "OUT", "OUT"

    challan_number = models.CharField(max_length=100, blank=True)
    challan_date = models.DateField()
    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="challans")
    job_description = models.CharField(max_length=255)
    job_type = models.CharField(max_length=100, blank=True)
    direction = models.CharField(max_length=3, choices=Direction.choices, default=Direction.INBOUND)
    weight_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)
    receipt_generated_at = models.DateTimeField(null=True, blank=True)
    source_batch = models.ForeignKey(
        "migration_app.MigrationBatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="imported_challans",
    )
    source_row_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-challan_date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["party", "challan_number"],
                condition=~models.Q(challan_number=""),
                name="uniq_party_challan_number",
            ),
        ]

    def __str__(self) -> str:
        return self.challan_number or f"Challan {self.pk}"

    def receipt_code(self) -> str:
        return f"CH-{self.pk}" if self.pk else ""

    receipt_code.short_description = "Receipt Code"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.receipt_generated_at:
            self.receipt_generated_at = self.receipt_generated_at or timezone.now()
            super().save(update_fields=["receipt_generated_at"])
