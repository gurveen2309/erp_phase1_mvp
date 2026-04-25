from __future__ import annotations

from django.conf import settings
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


class ProcessReport(models.Model):
    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="process_reports")
    invoice = models.ForeignKey(
        "finance.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_reports",
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_reports",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    ref_no = models.CharField(max_length=100, blank=True)
    dated = models.DateField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    part_name = models.CharField(max_length=255, blank=True)
    hardness = models.CharField(max_length=100, blank=True)
    sample_id = models.CharField(max_length=100, blank=True)
    material_grade = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=100, blank=True)
    hardening_temp = models.CharField(max_length=100, blank=True)
    hardening_speed = models.CharField(max_length=100, blank=True)
    hardening_hrc = models.CharField(max_length=100, blank=True)
    quenching_media = models.CharField(max_length=100, blank=True)
    quenching_temp = models.CharField(max_length=100, blank=True)
    tempering_temp = models.CharField(max_length=100, blank=True)
    tempering_speed = models.CharField(max_length=100, blank=True)
    tempering_hrc = models.CharField(max_length=100, blank=True)

    pdf = models.FileField(upload_to="reports/process/%Y/%m/", null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["party", "-generated_at"]),
        ]

    def __str__(self) -> str:
        return f"Process Report #{self.pk} — {self.party.name}"


class InspectionReport(models.Model):
    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="inspection_reports")
    invoice = models.ForeignKey(
        "finance.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspection_reports",
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspection_reports",
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    date = models.DateField(null=True, blank=True)
    part_name = models.CharField(max_length=255, blank=True)
    no = models.CharField(max_length=100, blank=True)
    lot_qty = models.CharField(max_length=100, blank=True)
    material_grade = models.CharField(max_length=100, blank=True)
    supplier_tc_received = models.CharField(max_length=100, blank=True)
    process_done = models.CharField(max_length=255, blank=True)
    ht = models.CharField(max_length=100, blank=True)

    hardness_spec = models.CharField(max_length=100, blank=True)
    micro_structure_spec = models.CharField(max_length=100, blank=True)
    grain_size_spec = models.CharField(max_length=100, blank=True)
    tensile_strength_spec = models.CharField(max_length=100, blank=True)
    other_requirements_spec = models.CharField(max_length=100, blank=True)

    hardness_obs_1 = models.CharField(max_length=50, blank=True)
    hardness_obs_2 = models.CharField(max_length=50, blank=True)
    hardness_obs_3 = models.CharField(max_length=50, blank=True)
    hardness_obs_4 = models.CharField(max_length=50, blank=True)
    hardness_obs_5 = models.CharField(max_length=50, blank=True)
    hardness_obs_6 = models.CharField(max_length=50, blank=True)
    hardness_obs_7 = models.CharField(max_length=50, blank=True)
    hardness_obs_8 = models.CharField(max_length=50, blank=True)

    micro_structure_obs_1 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_2 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_3 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_4 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_5 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_6 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_7 = models.CharField(max_length=50, blank=True)
    micro_structure_obs_8 = models.CharField(max_length=50, blank=True)

    grain_size_obs_1 = models.CharField(max_length=50, blank=True)
    grain_size_obs_2 = models.CharField(max_length=50, blank=True)
    grain_size_obs_3 = models.CharField(max_length=50, blank=True)
    grain_size_obs_4 = models.CharField(max_length=50, blank=True)
    grain_size_obs_5 = models.CharField(max_length=50, blank=True)
    grain_size_obs_6 = models.CharField(max_length=50, blank=True)
    grain_size_obs_7 = models.CharField(max_length=50, blank=True)
    grain_size_obs_8 = models.CharField(max_length=50, blank=True)

    tensile_strength_obs_1 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_2 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_3 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_4 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_5 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_6 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_7 = models.CharField(max_length=50, blank=True)
    tensile_strength_obs_8 = models.CharField(max_length=50, blank=True)

    other_obs_1 = models.CharField(max_length=50, blank=True)
    other_obs_2 = models.CharField(max_length=50, blank=True)
    other_obs_3 = models.CharField(max_length=50, blank=True)
    other_obs_4 = models.CharField(max_length=50, blank=True)
    other_obs_5 = models.CharField(max_length=50, blank=True)
    other_obs_6 = models.CharField(max_length=50, blank=True)
    other_obs_7 = models.CharField(max_length=50, blank=True)
    other_obs_8 = models.CharField(max_length=50, blank=True)

    qty_checked = models.CharField(max_length=50, blank=True)
    qty = models.CharField(max_length=50, blank=True)

    pdf = models.FileField(upload_to="reports/inspection/%Y/%m/", null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["party", "-generated_at"]),
        ]

    def __str__(self) -> str:
        return f"Inspection Report #{self.pk} — {self.party.name}"
