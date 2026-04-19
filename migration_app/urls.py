from django.urls import path

from migration_app import views


app_name = "migration_app"

urlpatterns = [
    path("", views.upload_import_view, name="upload"),
    path("confirm/", views.confirm_import_view, name="confirm"),
    path("history/", views.batch_history_view, name="history"),
    path("batch/<int:batch_id>/errors.csv", views.download_errors_view, name="download-errors"),
]
