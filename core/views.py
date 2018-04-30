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
    querystring = request.GET.copy()
    page_number = querystring.pop('page', ['1'])[0].strip() or '1'
    search_query = request.GET.get('search')
    order_by = querystring.pop('order-by', [''])
    order_by = [field.strip().lower()
                for field in order_by[0].split(',')
                if field.strip()]

    if search_query:
        all_data = all_data.filter(search_data=SearchQuery(search_query))
    if querystring:
        all_data = all_data.apply_filters(querystring)

    all_data = all_data.apply_ordering(order_by)

    paginator = Paginator(all_data, 20)
    try:
        page = int(page_number)
    except ValueError:
        raise HttpResponseBadRequest
    data = paginator.get_page(page)

    if order_by:
        querystring['order-by'] = ','.join(order_by)
    if search_query:
        querystring['search'] = search_query
    context = {
        'total_count': all_data.count(),
        'data': data,
        'dataset': dataset,
        'fields': fields,
        'search_query': search_query,
        'querystring': querystring.urlencode(),
        'table': table,
        'version': version,
    }
    return render(request, 'dataset-detail.html', context)

def dataset_list(request):
    context = {'datasets': Dataset.objects.filter(show=True).order_by('name')}
    return render(request, 'dataset-list.html', context)

def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})

def index(request):
    return redirect(reverse('core:dataset-list'))

def manifesto(request):
    return render(request, 'manifesto.html', {})
