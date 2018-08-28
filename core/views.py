import csv
import uuid

from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.models import Dataset, Table
from core.templatetags.utils import obfuscate


max_export_rows = 350000

class Echo:
    def write(self, value):
        return value


def contact(request):
    return render(request, 'contact.html', {})


def queryset_to_csv(data, fields):
    header = None
    for row in data.iterator():
        row_data = {}
        for field in fields:
            if not field.show_on_frontend or field.name == 'search_data':
                continue
            else:
                value = getattr(row, field.name)
                if field.obfuscate:
                    value = obfuscate(value)
                row_data[field.name] = value
        if header is None:
            header = list(row_data.keys())
            yield header
        yield [row_data[field] for field in header]


def index(request):
    return redirect(reverse('core:home'))


def donate(request):
    return redirect('https://apoia.se/brasilio')


def home(request):
    context = {
        'datasets': Dataset.objects.filter(show=True).order_by('?')[:6],
    }
    return render(request, 'home.html', context)


def dataset_list(request):
    context = {
        'datasets': Dataset.objects.filter(show=True).order_by('name'),
    }
    return render(request, 'dataset-list.html', context)


def dataset_detail(request, slug, tablename=''):
    dataset = get_object_or_404(Dataset, slug=slug)
    if not tablename:
        tablename = dataset.get_default_table().name
        return redirect(reverse('core:dataset-table-detail',
                                kwargs={'slug': slug, 'tablename': tablename}))

    try:
        table = dataset.get_table(tablename)
    except Table.DoesNotExist:
        return HttpResponseBadRequest(f'Table does not exist.', status=404)

    version = dataset.version_set.order_by('-order').first()
    fields = table.fields
    fieldnames_to_show = [field.name
                          for field in fields
                          if field.show_on_frontend]
    # TODO: may move this logic to model
    querystring = request.GET.copy()
    page_number = querystring.pop('page', ['1'])[0].strip() or '1'
    search_query = querystring.pop('search', [''])[0]
    order_by = querystring.pop('order-by', [''])
    order_by = [field.strip().lower()
                for field in order_by[0].split(',')
                if field.strip()]
    download_csv = querystring.get('format', '') == 'csv'
    all_data = table.get_model().objects
    if not download_csv:
        all_data = all_data.values(*fieldnames_to_show)

    if search_query:
        all_data = all_data.search(search_query)
    if querystring:
        all_data = all_data.apply_filters(
            {key: value for key, value in querystring.items() if value}
        )

    all_data = all_data.apply_ordering(order_by)
    if download_csv and 0 < all_data.count() <= max_export_rows:
        filename = '{}-{}.csv'.format(slug, uuid.uuid4().hex)
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer, dialect=csv.excel)
        csv_rows = queryset_to_csv(all_data, fields)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in csv_rows),
            content_type='text/csv;charset=UTF-8',
        )
        response['Content-Disposition'] = ('attachment; filename="{}"'
                                           .format(filename))
        response.encoding = 'UTF-8'
        return response


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
        'data': data,
        'dataset': dataset,
        'table': table,
        'fields': fields,
        'max_export_rows': max_export_rows,
        'query_dict': querystring,
        'querystring': querystring.urlencode(),
        'search_query': search_query,
        'slug': slug,
        'table': table,
        'total_count': all_data.count(),
        'version': version,
    }
    return render(request, 'dataset-detail.html', context)


def dataset_suggestion(request):
    return render(request, 'dataset-suggestion.html', {})


def manifesto(request):
    return render(request, 'manifesto.html', {})


def collaborate(request):
    return render(request, 'collaborate.html', {})

def contribuidores(request):
    return render(request, 'contribuidores.html', {})
