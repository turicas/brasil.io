from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.models import Dataset


def contact(request):
    return render(request, 'contact.html', {})

def dataset_detail(request, slug):
    dataset = get_object_or_404(Dataset, slug=slug)
    version = dataset.version_set.order_by('-order').first()
    table = version.table_set.get(default=True)
    fields = table.field_set.all()
    context = {
        'dataset': dataset,
        'fields': fields,
        'table': table,
        'version': version,
    }
    return render(request, 'dataset-detail.html', context)

def dataset_list(request):
    context = {'datasets': Dataset.objects.all()}
    return render(request, 'dataset-list.html', context)

def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})

def index(request):
    return redirect(reverse('core:dataset-list'))

def manifesto(request):
    return render(request, 'manifesto.html', {})
