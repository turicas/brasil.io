from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from core.models import Dataset, Table
from .models import ClippingRelation


@login_required
def get_contenttype_instances(request):
    try:
        pk = int(request.GET.get("id"))
        content_type = ContentType.objects.get(id=pk)
        if content_type.app_label == "core" and content_type.model == "dataset":
            result = list(
                Dataset.objects
                .values("id", "name", "slug")
                .order_by("slug")
            )
            for item in result:
                item["name"] = f"{item['slug']} ({item['name']})"
                del item["slug"]
        elif content_type.app_label == "core" and content_type.model == "table":
            result = list(
                Table.objects.select_related("dataset")
                .values("id", "name", "dataset__slug")
                .order_by("dataset__slug", "name")
            )
            for item in result:
                item["name"] = f"{item['dataset__slug']}.{item['name']}"
                del item["dataset__slug"]
        else:
            return JsonResponse({"error": "Invalid content type ID"}, status=400)
        return JsonResponse(result, safe=False)
    except (ValueError, ObjectDoesNotExist):
        return JsonResponse({"error": "Invalid content type ID"}, status=400)

@login_required
def get_current_selected_instance(request):
    try:
        pk = int(request.GET.get("id"))
        result = ClippingRelation.objects.get(id=pk).object_id
        return JsonResponse({"object_id": result})
    except (ValueError, ObjectDoesNotExist):
        return JsonResponse({"error": "Invalid clipping relation ID"}, status=400)
