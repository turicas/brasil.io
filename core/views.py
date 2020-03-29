import csv
import uuid

import pytz
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from core.forms import ContactForm, DatasetSearchForm
from core.models import Dataset, Table
from core.templatetags.utils import obfuscate
from core.util import brasilio_github_contributors


max_export_rows = 350_000
TIMEZONE = pytz.timezone("America/Sao_Paulo")


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
                subject="Contato no Brasil.IO",
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
        table = dataset.get_table(tablename)
    except Table.DoesNotExist:
        context = {"message": "Table does not exist"}
        return render(request, "404.html", context, status=404)

    querystring = request.GET.copy()
    page_number = querystring.pop("page", ["1"])[0].strip() or "1"
    items_per_page = querystring.pop("items", [str(settings.ROWS_PER_PAGE)])[
        0
    ].strip() or str(settings.ROWS_PER_PAGE)
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

    all_data = table.get_model().objects.filter_by_querystring(querystring)

    if download_csv:
        if all_data.count() > max_export_rows:
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

    import_date = table.import_date
    # TODO: use Django's timezone system
    if import_date.tzinfo is None:
        import_date = TIMEZONE.localize(import_date)
    else:
        import_date = import_date.replace(tzinfo=TIMEZONE)
    context = {
        "collected_at": version.collected_at,
        "data": data,
        "dataset": dataset,
        "fields": fields,
        "import_date": import_date,
        "max_export_rows": max_export_rows,
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
    return render(
        request, "contributors.html", {"contributors": brasilio_github_contributors()}
    )
