from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap default ERP role groups and permissions."

    def handle(self, *args, **options):
        roles = {
            "OwnerAdmin": None,
            "Accountant": [
                "add_openingbalance",
                "change_openingbalance",
                "delete_openingbalance",
                "view_openingbalance",
                "add_invoice",
                "change_invoice",
                "delete_invoice",
                "view_invoice",
                "add_payment",
                "change_payment",
                "delete_payment",
                "view_payment",
                "view_migrationbatch",
                "view_migrationrowerror",
                "view_approvalrequest",
                "view_auditevent",
                "view_backupsnapshot",
                "view_audit_log",
            ],
            "Operator": [
                "add_party",
                "change_party",
                "view_party",
                "add_challan",
                "change_challan",
                "view_challan",
                "view_openingbalance",
                "view_invoice",
                "view_payment",
                "view_migrationbatch",
                "view_migrationrowerror",
            ],
            "Viewer": [
                "view_party",
                "view_challan",
                "view_openingbalance",
                "view_invoice",
                "view_payment",
                "view_migrationbatch",
                "view_migrationrowerror",
                "view_approvalrequest",
                "view_auditevent",
                "view_backupsnapshot",
                "view_audit_log",
            ],
        }

        all_permissions = Permission.objects.all()
        for group_name, codenames in roles.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            if codenames is None:
                group.permissions.set(all_permissions)
            else:
                perms = Permission.objects.filter(codename__in=codenames)
                group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"Configured group: {group_name}"))

        self.stdout.write(
            self.style.WARNING(
                "Assign users to groups manually in Django admin and set is_staff=True for users who should access admin/custom pages."
            )
        )

