import csv
import uuid

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import ContactForm
from core.models import Dataset, Table
from core.templatetags.utils import obfuscate
from core.util import github_repository_contributors


max_export_rows = 350_000


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
        return HttpResponseBadRequest(f"Invalid HTTP method.", status=404)

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
    context = {"datasets": Dataset.objects.filter(show=True).order_by("name")}
    return render(request, "dataset-list.html", context)


def dataset_detail(request, slug, tablename=""):
    dataset = get_object_or_404(Dataset, slug=slug)
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
        return HttpResponseBadRequest(f"Table does not exist.", status=404)

    querystring = request.GET.copy()
    page_number = querystring.pop("page", ["1"])[0].strip() or "1"
    download_csv = querystring.pop("format", [""]) == ["csv"]
    try:
        page = int(page_number)
    except ValueError:
        return HttpResponseBadRequest("Invalid page number.", status=404)

    version = dataset.version_set.order_by("-order").first()
    fields = table.fields

    all_data = table.get_model().objects.filter_by_querystring(querystring)

    if not download_csv:
        fieldnames_to_show = [field.name for field in fields if field.show_on_frontend]
        all_data = all_data.values(*fieldnames_to_show)
    else:
        if all_data.count() <= max_export_rows:
            filename = "{}-{}.csv".format(slug, uuid.uuid4().hex)
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer, dialect=csv.excel)
            csv_rows = queryset_to_csv(all_data, fields)
            response = StreamingHttpResponse(
                (writer.writerow(row) for row in csv_rows),
                content_type="text/csv;charset=UTF-8",
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                filename
            )
            response.encoding = "UTF-8"
            return response
        else:
            return HttpResponseBadRequest("Max rows exceeded.", status=404)

    paginator = Paginator(all_data, 20)
    data = paginator.get_page(page)

    for key, value in list(querystring.items()):
        if not value:
            del querystring[key]
    context = {
        "data": data,
        "dataset": dataset,
        "table": table,
        "fields": fields,
        "max_export_rows": max_export_rows,
        "query_dict": querystring,
        "querystring": querystring.urlencode(),
        "slug": slug,
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
        request,
        "contributors.html",
        {"contributors": github_repository_contributors("turicas", "brasil.io")},
    )
