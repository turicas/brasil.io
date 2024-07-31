import json

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse

from .models import ClippingRelation


def get_contenttype_instances(request):
    pk = request.GET.get("id")
    result = list(ContentType.objects.get(id=pk).model_class().objects.filter().values("id", "name"))
    return HttpResponse(json.dumps(result), content_type="application/json")


def get_current_selected_instance(request):
    pk = request.GET.get("id")
    result = ClippingRelation.objects.get(id=pk).object_id
    return HttpResponse(json.dumps(result), content_type="application/json")
