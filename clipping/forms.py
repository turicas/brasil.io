from django import forms
from django.conf import settings
from django.forms import ModelForm

from .models import Clipping


class ClippingForm(ModelForm):
    category = forms.CharField(widget=forms.Select(choices=settings.CATEGORY_CHOICES), label="Categoria")
    date = forms.CharField(widget=forms.TextInput(attrs={"class": "datepicker"}), label="Data")
    author = forms.CharField(label="Autor")
    title = forms.CharField(label="Título")

    class Meta:
        model = Clipping
        fields = "__all__"
        exclude = ["added_by", "published"]
