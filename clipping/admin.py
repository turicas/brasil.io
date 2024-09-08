from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelChoiceField

from .models import Clipping, ClippingRelation

TARGET_MODELS = {"core": ["dataset", "table"]}


TARGET_MODELS = {
    "core": ["dataset", "table"]
}


class ClippingRelationAdminForm(forms.ModelForm):
    contents = []
    for app_name in TARGET_MODELS:
        for model_name in TARGET_MODELS[app_name]:
            contents.append(model_name)

    content_type = ModelChoiceField(
        ContentType.objects.filter(app_label__in=TARGET_MODELS, model__in=contents),
        empty_label="--------",
        label="Content",
    )
    object_id = forms.CharField(widget=forms.Select(choices=[("", "---------")]), label="Element")

    class Meta:
        model = ClippingRelation
        fields = ["content_type", "object_id", "clipping"]


@admin.register(ClippingRelation)
class ClippingRelationAdmin(admin.ModelAdmin):
    form = ClippingRelationAdminForm
    list_display = (
        "id",
        "content_type",
        "get_clipping_relation",
        "clipping",
    )

    def get_clipping_relation(self, obj):
        content_type = obj.content_type
        content_object = obj.content_object

        if content_type.model == "dataset":
            return f"{content_object.slug} ({content_object.name})"
        elif content_type.model == "table":
            return f"{content_object.dataset.slug}.{content_object.name}"
        else:
            return str(content_object)

    get_clipping_relation.short_description = "Relation"


class ClippingAdminForm(forms.ModelForm):
    category = forms.CharField(widget=forms.Select(choices=Clipping.CategoryChoices.choices), label="Category")

    class Meta:
        model = Clipping
        exclude = ["added_by"]


@admin.register(Clipping)
class ClippingAdmin(admin.ModelAdmin):
    form = ClippingAdminForm
    list_display = ("date", "title", "author", "vehicle", "category", "url", "added_by", "published")

    def save_model(self, request, obj, form, change):
        if getattr(obj, "added_by", None) is None:
            obj.added_by = request.user
        obj.save()
