import csv
import uuid

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.commands import UpdateTableFileListCommand
from core.forms import ContactForm, DatasetSearchForm
from core.models import Dataset, Table
from core.templatetags.utils import obfuscate
from core.util import cached_http_get_json, get_cached_apoiase_donors
from utils.file_info import human_readable_size


class Echo:
    def write(self, value):
        return value


def contact(request):
    sent = request.GET.get("sent", "").lower() == "true"

    if request.method == "GET":
        data = {}
        if request.user and not request.user.is_anonymous:
            data["name"] = request.user.first_name or request.user.username
            data["email"] = request.user.email
        form = ContactForm(data=data)

    elif request.method == "POST":
        form = ContactForm(data=request.POST)

        if form.is_valid():
            data = form.cleaned_data
            email = EmailMessage(
                subject=f"Contato no Brasil.IO: {data['name']}",
                body=data["message"],
                from_email=f'{data["name"]} (via Brasil.IO) <{settings.DEFAULT_FROM_EMAIL}>',
                to=[settings.DEFAULT_FROM_EMAIL],
                reply_to=[f'{data["name"]} <{data["email"]}>'],
            )
            email.send()
            return redirect(reverse("core:contact") + "?sent=true")

    else:
        context = {"message": "Invalid HTTP method."}
        return render(request, "404.html", context, status=400)

    return render(request, "contact.html", {"form": form, "sent": sent})


def queryset_to_csv(data, fields):
    header = None
    for row in data.iterator():
        row_data = {}
        for field in fields:
            if not field.show_on_frontend or field.name == "search_data":
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
    return redirect(reverse("core:home"))


def donate(request):
    return redirect("https://apoia.se/brasilio")


def home(request):
    context = {"datasets": Dataset.objects.filter(show=True).order_by("?")[:6]}
    return render(request, "home.html", context)


def dataset_list(request):
    form = DatasetSearchForm(request.GET)
    q = Q(show=True)
    if form.is_valid():
        search_str = form.cleaned_data["search"]
        for term in search_str.split(" "):
            q &= Q(Q(description__icontains=term) | Q(name__icontains=term))
    context = {"datasets": Dataset.objects.filter(q).order_by("name"), "form": form}
    return render(request, "dataset-list.html", context)


def dataset_detail(request, slug, tablename=""):
    try:
        dataset = Dataset.objects.get(slug=slug)
    except Dataset.DoesNotExist:
        context = {"message": "Dataset does not exist"}
        return render(request, "404.html", context, status=404)

    if not tablename:
        tablename = dataset.get_default_table().name
        return redirect(
            reverse(
                "core:dataset-table-detail",
                kwargs={"slug": slug, "tablename": tablename},
            )
        )

    try:
        allow_hidden = request.user.is_superuser
        table = dataset.get_table(tablename, allow_hidden=allow_hidden)
    except Table.DoesNotExist:
        context = {"message": "Table does not exist"}
        return render(request, "404.html", context, status=404)

    querystring = request.GET.copy()
    page_number = querystring.pop("page", ["1"])[0].strip() or "1"
    items_per_page = querystring.pop("items", [str(settings.ROWS_PER_PAGE)])[0].strip() or str(settings.ROWS_PER_PAGE)
    download_csv = querystring.pop("format", [""]) == ["csv"]
    try:
        page = int(page_number)
    except ValueError:
        context = {"message": "Invalid page number."}
        return render(request, "404.html", context, status=404)
    try:
        items_per_page = int(items_per_page)
    except ValueError:
        context = {"message": "Invalid items per page."}
        return render(request, "404.html", context, status=404)
    items_per_page = min(items_per_page, 1000)

    version = dataset.version_set.order_by("-order").first()
    fields = table.fields

    TableModel = table.get_model()
    query, search_query, order_by = TableModel.objects.parse_querystring(querystring)
    all_data = TableModel.objects.composed_query(query, search_query, order_by)

    if download_csv:
        user_agent = request.headers.get("User-Agent", "")
        block_agent = any(True for agent in settings.BLOCKED_AGENTS if agent.lower() in user_agent.lower())

        if not any([query, search_query]) or not user_agent or block_agent:
            # User trying to download a CSV without custom filters or invalid
            # user-agent specified.
            context = {"html_content": "400-csv-without-filters.html", "download_url": table.version.download_url}
            return render(request, "404.html", context, status=400)

        if all_data.count() > settings.CSV_EXPORT_MAX_ROWS:
            context = {"message": "Max rows exceeded."}
            return render(request, "404.html", context, status=400)

        filename = "{}-{}.csv".format(slug, uuid.uuid4().hex)
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer, dialect=csv.excel)
        csv_rows = queryset_to_csv(all_data, fields)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in csv_rows),
            content_type="text/csv;charset=UTF-8",
        )
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
        response.encoding = "UTF-8"
        return response

    paginator = Paginator(all_data, items_per_page)
    data = paginator.get_page(page)

    for key, value in list(querystring.items()):
        if not value:
            del querystring[key]

    context = {
        "data": data,
        "dataset": dataset,
        "fields": fields,
        "max_export_rows": settings.CSV_EXPORT_MAX_ROWS,
        "query_dict": querystring,
        "querystring": querystring.urlencode(),
        "slug": slug,
        "table": table,
        "table": table,
        "total_count": all_data.count(),
        "version": version,
    }
    return render(request, "dataset-detail.html", context)


def dataset_suggestion(request):
    return render(request, "dataset-suggestion.html", {})


def manifesto(request):
    return render(request, "manifesto.html", {})


def collaborate(request):
    return render(request, "collaborate.html", {})


def contributors(request):
    url = "https://data.brasil.io/meta/contribuidores.json"
    data = cached_http_get_json(url, 5)
    return render(request, "contributors.html", {"contributors": data})


def dataset_tables_files_detail(request, slug):
    # this view exists for admin users to quickly preview how data.brasil.io/dataset/<dataset_slug>/_meta/list.html will look like
    if not request.user.is_superuser:
        raise Http404

    dataset = get_object_or_404(Dataset, slug=slug)
    tables = dataset.tables
    capture_date = max([t.collect_date for t in tables])

    sha_sums, content = dataset.sha512sums
    fname = settings.MINIO_DATASET_SHA512SUMS_FILENAME
    dest_name = f"{dataset.slug}/{fname}"
    sha512sums_file = UpdateTableFileListCommand.FileListInfo(
        filename=fname,
        readable_size=human_readable_size(len(content.encode())),
        sha512sum=sha_sums,
        file_url=f"{settings.AWS_S3_ENDPOINT_URL}{settings.MINIO_STORAGE_MEDIA_BUCKET_NAME}/{dest_name}",
    )

    context = {
        "dataset": dataset,
        "capture_date": capture_date,
        "file_list": dataset.tables_files + [sha512sums_file],
    }
    return render(request, "tables_files_list.html", context)


def donors(request):
    page = request.GET.get("page", 1)
    paginator = Paginator(get_cached_apoiase_donors(), 25)
    data = paginator.page(page)
    return render(request, "donors.html", {"donors": data})