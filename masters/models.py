from __future__ import annotations

from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    gst_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    source_batch = models.ForeignKey(
        "migration_app.MigrationBatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="imported_parties",
    )
    source_row_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
