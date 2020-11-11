from django.shortcuts import render

from core.models import Dataset


def dynamic_api_docs_view(request):
    context = {
        "datasets": Dataset.objects.api_visible(),
    }
    return render(request, "api/docs.html", context=context)
