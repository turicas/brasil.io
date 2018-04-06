from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.urls import reverse
from django.forms.models import model_to_dict

from core.models import Dataset


def contact(request):
    return render(request, 'contact.html', {})

def dataset(request, slug):
    dataset = Dataset.objects.get(slug=slug)
    data = model_to_dict(dataset)
    data['links'] = [model_to_dict(link) for link in dataset.link_set.all()]
    return JsonResponse(data)

def dataset_list(request):
    return JsonResponse({'data': [model_to_dict(dataset)
                                  for dataset in Dataset.objects.all()]})

def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})

def index(request):
    return redirect(reverse('core:dataset-list'))

def manifesto(request):
    return render(request, 'manifesto.html', {})
