from django import forms
from django.conf import settings
from django.forms import ModelForm

from .models import Clipping


class ClippingForm(ModelForm):
    category = forms.CharField(
        widget=forms.Select(
            attrs={
                'aria-label': 'Seletor de categoria',
                'class':'form-select'
            },
            choices=settings.CATEGORY_CHOICES
        ), 
        label="Categoria"
    )
    date = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type":"text",
                "class":"datepicker_input form-control",
                "placeholder":"aaaa/mm/dd",
                "autocomplete":"off",
            }
        ), 
        label="Data"
    )
    vehicle = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type':'text',
                'class':"form-control",
                "placeholder":"Veículo que exibiu o conteúdo",
            }
        ),
        label="Veículo"
    )
    author = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type':'text',
                'class':"form-control",
                "placeholder":"Autor do conteúdo",
            }
        ),
        label="Autor"
    )
    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type':'text',
                'class':"form-control",
                "placeholder":"Título do conteúdo",
            }
        ),
        label="Título"
    )
    url = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type':'url',
                'class':"form-control",
                "placeholder":"http://site.com",
            }
        ),
        label="URL"
    )

    class Meta:
        model = Clipping
        fields = "__all__"
        exclude = ["added_by", "published"]
