from django.contrib.postgres.search import SearchQuery
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
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
    all_data = dataset.get_last_data_model().objects.all()
    query = request.GET.get('q')
    if query:
        all_data = all_data.filter(search_data=SearchQuery(query))

    paginator = Paginator(all_data, 20)
    try:
        page = int(request.GET.get('page', 1) or 1)
    except ValueError:
        raise HttpResponseBadRequest
    data = paginator.get_page(page)

    context = {
        'start_count': (data.number - 1) * data.paginator.per_page + 1,
        'end_count': data.number * data.paginator.per_page,
        'total_count': all_data.count(),
        'data': data,
        'dataset': dataset,
        'fields': fields,
        'query': query,
        'table': table,
        'version': version,
    }
    return render(request, 'dataset-detail.html', context)

def dataset_list(request):
    context = {'datasets': Dataset.objects.filter(show=True)}
    return render(request, 'dataset-list.html', context)

def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})

def index(request):
    return redirect(reverse('core:dataset-list'))

def manifesto(request):
    return render(request, 'manifesto.html', {})
