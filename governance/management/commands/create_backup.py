from __future__ import annotations

from django.core.management.base import BaseCommand

from governance.services import create_backup_snapshot


class Command(BaseCommand):
    help = "Create a database backup snapshot."

    def add_arguments(self, parser):
        parser.add_argument("--notes", default="")
        parser.add_argument("--backup-type", default="manual")

    def handle(self, *args, **options):
        snapshot = create_backup_snapshot(backup_type=options["backup_type"], notes=options["notes"])
        self.stdout.write(self.style.SUCCESS(f"Created backup snapshot #{snapshot.id}: {snapshot.file_path}"))

