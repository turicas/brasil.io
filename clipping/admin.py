from django import forms
from django.contrib import admin
from django.forms.models import ModelChoiceField

from .models import ClippingRelation, Clipping
from django.contrib.contenttypes.models import ContentType

from django.conf import settings


class ClippingRelationAdminForm(forms.ModelForm):
    contents = []
    for app_name in settings.CONTENTS:
        for model_name in settings.CONTENTS[app_name]:
            contents.append(model_name)

    content_type = ModelChoiceField(ContentType.objects.filter(app_label__in=settings.CONTENTS, model__in=contents),
                                    empty_label="--------", label='Content')
    object_id = forms.CharField(widget=forms.Select(choices=[('','---------')]), label='Element')

    class Meta:
        model = ClippingRelation
        fields = ['content_type', 'object_id', 'clipping']


@admin.register(ClippingRelation)
class ClippingRelationAdmin(admin.ModelAdmin):
    form = ClippingRelationAdminForm
    list_display = ('get_clipping_relation', 'clipping', 'content_type')

    def get_clipping_relation(self, obj):
        return obj.content_object.name
    get_clipping_relation.short_description = 'Relation'


class ClippingAdminForm(forms.ModelForm):
    category = forms.CharField(widget=forms.Select(choices=settings.CATEGORY_CHOICES), label='Category')

    class Meta:
        model = Clipping
        exclude = ['added_by']


@admin.register(Clipping)
class ClippingAdmin(admin.ModelAdmin):
    form = ClippingAdminForm
    list_display = ('date','title', 'author', 'vehicle', 'category', 'url', 'added_by', 'published')

    # Sets the current user as the adder
    def save_model(self, request, obj, form, change):
        if getattr(obj, 'added_by', None) is None:
            obj.added_by = request.user
        obj.save()
