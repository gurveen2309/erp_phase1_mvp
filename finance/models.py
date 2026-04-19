from __future__ import annotations

from django.db import models


class ImportedModelMixin(models.Model):
    source_batch = models.ForeignKey(
        "migration_app.MigrationBatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)ss",
    )
    source_row_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OpeningBalance(ImportedModelMixin):
    class BalanceType(models.TextChoices):
        DEBIT = "DR", "Debit"
        CREDIT = "CR", "Credit"

    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="opening_balances")
    effective_date = models.DateField()
    balance_type = models.CharField(max_length=2, choices=BalanceType.choices, default=BalanceType.DEBIT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["effective_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["party", "effective_date", "balance_type", "amount"],
                name="uniq_opening_balance_signature",
            )
        ]

    def __str__(self) -> str:
        return f"{self.party} opening {self.amount}"


class Invoice(ImportedModelMixin):
    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["invoice_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["party", "invoice_number"],
                condition=~models.Q(invoice_number=""),
                name="uniq_party_invoice_number",
            )
        ]

    def __str__(self) -> str:
        return self.invoice_number or f"Invoice {self.pk}"


class Payment(ImportedModelMixin):
    class Mode(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank"
        CHEQUE = "cheque", "Cheque"
        ADJUSTMENT = "adjustment", "Adjustment"

    party = models.ForeignKey("masters.Party", on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.BANK)
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["payment_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["party", "reference_number"],
                condition=~models.Q(reference_number=""),
                name="uniq_party_payment_reference",
            )
        ]

    def __str__(self) -> str:
        return self.reference_number or f"Payment {self.pk}"
