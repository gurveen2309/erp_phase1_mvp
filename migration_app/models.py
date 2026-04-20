from __future__ import annotations

from django.conf import settings
from django.db import models


class MigrationBatch(models.Model):
    class Status(models.TextChoices):
        PREVIEW = "preview", "Preview"
        IMPORTED = "imported", "Imported"
        FAILED = "failed", "Failed"
        ROLLED_BACK = "rolled_back", "Rolled Back"

    class FileType(models.TextChoices):
        XLSX = "xlsx", "XLSX"
        CSV = "csv", "CSV"

    class ImportType(models.TextChoices):
        PARTIES = "parties", "Parties"
        OPENING_BALANCES = "opening_balances", "Opening Balances"
        INVOICES = "invoices", "Invoices"
        PAYMENTS = "payments", "Payments"
        CHALLANS = "challans", "Challans"
        PRODUCTION_DASHBOARD_WORKBOOK = "production_dashboard_workbook", "Production Dashboard Workbook"

    source_file_name = models.CharField(max_length=255)
    upload = models.FileField(upload_to="imports/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREVIEW)
    import_type = models.CharField(max_length=30, choices=ImportType.choices)
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.XLSX)
    row_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    rolled_back_at = models.DateTimeField(null=True, blank=True)
    rolled_back_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rolled_back_migration_batches",
    )
    rollback_notes = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="migration_batches",
    )

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self) -> str:
        return f"{self.source_file_name} ({self.get_status_display()})"


class MigrationRowError(models.Model):
    batch = models.ForeignKey(MigrationBatch, on_delete=models.CASCADE, related_name="row_errors")
    row_number = models.PositiveIntegerField()
    sheet_name = models.CharField(max_length=100, blank=True)
    raw_payload = models.JSONField(default=dict)
    error_message = models.TextField()

    class Meta:
        ordering = ["row_number", "id"]

    def __str__(self) -> str:
        return f"Row {self.row_number}: {self.error_message}"


class MigrationMappingProfile(models.Model):
    import_type = models.CharField(max_length=30, choices=MigrationBatch.ImportType.choices)
    name = models.CharField(max_length=100)
    column_mapping_config = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["import_type", "name"]
        unique_together = [("import_type", "name")]

    def __str__(self) -> str:
        return f"{self.import_type}: {self.name}"
