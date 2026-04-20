from django.contrib import admin

from migration_app.models import MigrationBatch, MigrationMappingProfile, MigrationRowError


class MigrationRowErrorInline(admin.TabularInline):
    model = MigrationRowError
    extra = 0
    readonly_fields = ("row_number", "sheet_name", "raw_payload", "error_message")
    can_delete = False


@admin.register(MigrationBatch)
class MigrationBatchAdmin(admin.ModelAdmin):
    list_display = (
        "source_file_name",
        "import_type",
        "status",
        "row_count",
        "success_count",
        "error_count",
        "uploaded_at",
        "imported_at",
        "rolled_back_at",
        "rolled_back_by",
    )
    list_filter = ("status", "import_type", "file_type")
    search_fields = ("source_file_name",)
    readonly_fields = (
        "uploaded_at",
        "imported_at",
        "row_count",
        "success_count",
        "error_count",
        "rolled_back_at",
        "rolled_back_by",
        "rollback_notes",
    )
    inlines = [MigrationRowErrorInline]


@admin.register(MigrationRowError)
class MigrationRowErrorAdmin(admin.ModelAdmin):
    list_display = ("batch", "row_number", "sheet_name", "error_message")
    search_fields = ("batch__source_file_name", "error_message")
    list_filter = ("sheet_name",)


@admin.register(MigrationMappingProfile)
class MigrationMappingProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "import_type", "is_default")
    list_filter = ("import_type", "is_default")
    search_fields = ("name",)
