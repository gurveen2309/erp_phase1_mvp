from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError

from finance.models import Payment
from governance.models import ApprovalRequest
from governance.services import create_approval_request
from masters.models import Party


class Command(BaseCommand):
    help = "Stage Gmail-extracted HDFC transactions as pending ApprovalRequests (DB only, no Gmail logic)."

    def add_arguments(self, parser):
        parser.add_argument("--data", type=str, required=True, help="JSON array of transaction objects")
        parser.add_argument("--dry-run", action="store_true", help="Print actions without writing to DB")
        parser.add_argument(
            "--clear-staged",
            action="store_true",
            help="Delete all pending ApprovalRequests with source=gmail_sync before staging",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        clear_staged: bool = options["clear_staged"]

        try:
            transactions: list[dict] = json.loads(options["data"])
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in --data: {exc}") from exc

        if not isinstance(transactions, list):
            raise CommandError("--data must be a JSON array")

        if clear_staged:
            qs = ApprovalRequest.objects.filter(metadata__source="gmail_sync", status=ApprovalRequest.Status.PENDING)
            count = qs.count()
            if not dry_run:
                qs.delete()
            self.stdout.write(f"{'[dry-run] Would clear' if dry_run else 'Cleared'} {count} staged gmail_sync request(s).")

        staged = skipped_dup = skipped_invalid = 0
        rows: list[tuple[str, str]] = []

        from finance.models import Payment  # noqa: F811 (already imported; explicit for clarity)

        for txn in transactions:
            gmail_id = txn.get("gmail_message_id", "")
            ref = txn.get("reference_number", "")
            txn_date = txn.get("transaction_date", "")
            amount_raw = txn.get("amount", "")
            direction = txn.get("direction", "")
            narration = txn.get("narration", "")
            party_id = txn.get("party_id")
            party_name = Party.objects.filter(pk=party_id).values_list("name", flat=True).first() if party_id else None
            mode = txn.get("mode", "bank")
            confidence = txn.get("confidence", 0)

            # Validate required fields
            try:
                amount = Decimal(str(amount_raw))
            except InvalidOperation:
                skipped_invalid += 1
                rows.append(("INVALID", f"bad amount '{amount_raw}' | {narration[:40]}"))
                continue

            if not gmail_id or not txn_date:
                skipped_invalid += 1
                rows.append(("INVALID", f"missing gmail_message_id or transaction_date | {narration[:40]}"))
                continue

            # Dedup: already a committed Payment with this reference
            if ref and Payment.objects.filter(reference_number=ref, payment_date=txn_date).exists():
                skipped_dup += 1
                rows.append(("SKIPPED", f"dup payment | ref={ref} | {narration[:40]}"))
                continue

            # Dedup: already staged (any status — a rejected record still means the email was processed)
            if ApprovalRequest.objects.filter(metadata__gmail_message_id=gmail_id).exists():
                skipped_dup += 1
                rows.append(("SKIPPED", f"already staged | msg={gmail_id[:12]} | {narration[:40]}"))
                continue

            if not dry_run:
                create_approval_request(
                    action_type=ApprovalRequest.ActionType.CREATE,
                    submitted_by=None,
                    model_class=Payment,
                    object_id=None,
                    before_snapshot={},
                    after_snapshot={
                        "party": party_id,
                        "party_name": party_name,
                        "payment_date": txn_date,
                        "amount": str(amount),
                        "mode": mode,
                        "reference_number": ref,
                        "remarks": f"Gmail sync | {narration} | msg:{gmail_id}",
                    },
                    metadata={
                        "gmail_message_id": gmail_id,
                        "direction": direction,
                        "confidence": confidence,
                        "narration": narration,
                        "source": "gmail_sync",
                    },
                    reason=f"HDFC Gmail sync — {direction} Rs.{amount} on {txn_date}",
                )

            staged += 1
            party_label = f"party_id={party_id}" if party_id else "UNMATCHED"
            rows.append(("STAGED", f"{direction} Rs.{amount} | {party_label} | conf={int(confidence*100)}% | {narration[:40]}"))

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(f"\n{prefix}Results: {staged} staged, {skipped_dup} skipped (dup), {skipped_invalid} invalid\n")
        for status, detail in rows:
            self.stdout.write(f"  {status:<10} {detail}")

        if not dry_run and staged:
            self.stdout.write("\nVisit /governance/approvals/ to review and approve staged transactions.")
