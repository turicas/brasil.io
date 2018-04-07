from django.shortcuts import redirect, render
from django.urls import reverse


def contact(request):
    return render(request, 'contact.html', {})

def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})

def index(request):
    return redirect(reverse('core:dataset-list'))

def manifesto(request):
    return render(request, 'manifesto.html', {})
