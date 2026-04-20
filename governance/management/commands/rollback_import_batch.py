from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from governance.services import rollback_import_batch
from migration_app.models import MigrationBatch


class Command(BaseCommand):
    help = "Roll back imported rows for a migration batch."

    def add_arguments(self, parser):
        parser.add_argument("batch_id", type=int)
        parser.add_argument("--notes", default="")

    def handle(self, *args, **options):
        try:
            batch = MigrationBatch.objects.get(pk=options["batch_id"])
        except MigrationBatch.DoesNotExist as exc:
            raise CommandError("Migration batch not found.") from exc
        rollback_import_batch(batch, notes=options["notes"])
        self.stdout.write(self.style.SUCCESS(f"Rolled back migration batch #{batch.id}"))

