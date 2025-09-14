# core/middleware.py
from django.utils import timezone

class BrowserTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.COOKIES.get("timezone")
        if tzname:
            try:
                timezone.activate(tzname)
            except Exception:
                timezone.deactivate()
        else:
            # default: keep project TZ (UTC in your settings)
            timezone.deactivate()
        return self.get_response(request)
