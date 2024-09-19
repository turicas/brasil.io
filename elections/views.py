from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from elections.filters import CandidacyFilterSet
from elections.models import Candidacy, CandidacyMetadata
from elections.serializers import DetailCandidacySerializer, ListCandidacySerializer
from elections.suggestions import create_search_suggestions
from elections.title_utils import candidacy_list_title


def filter_selected_fields(filter_data):
    data = filter_data.dict()
    data.pop("format", None)
    for key in ("cargo", "uf", "partido"):
        if data.get(key) is None:
            data[key] = "Todos"

    if data.get("t") is None:
        data["t"] = "cidade"

    data.pop("ano", None)

    return data


def candidacy_list(request):
    # TODO: safe coercion
    page_size = int(request.GET.get("page_size", 40))
    filter_set = CandidacyFilterSet(request.GET, queryset=Candidacy.objects.all())
    paginator = Paginator(filter_set.qs, page_size)
    page = request.GET.get("page", 1)
    objs = paginator.page(page).object_list
    serializer = ListCandidacySerializer(objs, many=True)
    metadata = CandidacyMetadata.objects.first().data

    selected_filter_fields = filter_selected_fields(filter_set.data)
    title = candidacy_list_title(
        **selected_filter_fields,
        ano="2024",
        ano_inicio=Candidacy.first_year()
    )

    data = {
        "items": serializer.data,
        "number": page,
        "num_pages": paginator.num_pages,
        "page_size": page_size,
        "filters": selected_filter_fields,
        "title": title,
    }

    if request.GET.get("format") == "json":
        return JsonResponse(data, safe=False)

    data["metadata"] = metadata

    return render(request, "elections/elections.html", context={"data": data})


def politic(request, ano, uf, municipio, cargo, nome):
    candidacy = get_object_or_404(
        Candidacy,
        ano=ano,
        sigla_unidade_federativa__iexact=uf,
        municipio_slug=municipio,
        cargo_slug=cargo,
        nome_urna_slug=nome,
    )
    metadata = CandidacyMetadata.objects.first().data
    serializer = DetailCandidacySerializer(candidacy)
    data = {"item": serializer.data, "info_list": candidacy.info_list}
    if request.GET.get("format") == "json":
        return JsonResponse(data=data)

    data["metadata"] = metadata

    return render(request, "elections/politic.html", context={"data": data})


def about(request, state=None):
    metadata = CandidacyMetadata.objects.first().data
    context = {"data": {"metadata": metadata, "suggestions": create_search_suggestions()}}
    return render(request, "elections/about.html", context)


def candidacy_redirect_2024(request):
    return redirect("elections:candidacy_list")
