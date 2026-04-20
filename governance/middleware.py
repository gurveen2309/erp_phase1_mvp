from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lock_path = Path(settings.MAINTENANCE_MODE_FILE)
        if lock_path.exists() and request.method not in {"GET", "HEAD", "OPTIONS"}:
            return HttpResponse("Maintenance in progress. Please retry shortly.", status=503)
        return self.get_response(request)

