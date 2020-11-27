from django.conf import settings
from django.shortcuts import render

from core.models import Dataset


def dynamic_api_docs_view(request):
    context = {
        "datasets": Dataset.objects.api_visible(),
        "api_host": settings.BRASILIO_API_HOST,
    }
    return render(request, "api/docs.html", context=context)
