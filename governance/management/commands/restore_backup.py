from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from governance.models import BackupSnapshot
from governance.services import restore_backup_snapshot


class Command(BaseCommand):
    help = "Restore a backup snapshot by id."

    def add_arguments(self, parser):
        parser.add_argument("snapshot_id", type=int)
        parser.add_argument("--notes", default="")

    def handle(self, *args, **options):
        try:
            snapshot = BackupSnapshot.objects.get(pk=options["snapshot_id"])
        except BackupSnapshot.DoesNotExist as exc:
            raise CommandError("Backup snapshot not found.") from exc

        restore_backup_snapshot(snapshot, notes=options["notes"])
        self.stdout.write(self.style.SUCCESS(f"Restored backup snapshot #{snapshot.id}"))
