from django.conf import settings
from rest_framework.authentication import get_authorization_header
from rest_framework.permissions import IsAuthenticated


class ApiIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, *args, **kwargs):
        if settings.ENABLE_API_AUTH:
            return super().has_permission(request, *args, **kwargs)
        elif get_authorization_header(request) and not request.user.is_authenticated:
            return False
        return True
