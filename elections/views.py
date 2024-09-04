from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from elections.filters import CandidacyFilterSet
from elections.models import Candidacy, CandidacyMetadata
from elections.serializers import DetailCandidacySerializer, ListCandidacySerializer


def filter_selected_fields(filter_data):
    data = filter_data.dict()
    data.pop("format", None)
    return data


def candidacy_list(request):
    # TODO: safe coercion
    page_size = int(request.GET.get("page_size", 10))
    filter_set = CandidacyFilterSet(request.GET, queryset=Candidacy.objects.all())
    paginator = Paginator(filter_set.qs, page_size)
    page = request.GET.get("page", 1)
    objs = paginator.page(page).object_list
    serializer = ListCandidacySerializer(objs, many=True)
    metadata = CandidacyMetadata.objects.first().data

    data = {
        "items": serializer.data,
        "number": page,
        "num_pages": paginator.num_pages,
        "page_size": page_size,
        "metadata": metadata,
        "filters": filter_selected_fields(filter_set.data),
    }

    if request.GET.get("format") == "json":
        return JsonResponse(data, safe=False)

    return render(request, "elections/elections.html", context={"data": data})


def politic(request, ano, uf, cargo, nome):
    candidacy = get_object_or_404(
        Candidacy,
        ano=ano,
        sigla_unidade_federativa__iexact=uf,
        cargo_slug=cargo,
        nome_urna_slug=nome,
    )
    serializer = DetailCandidacySerializer(candidacy)
    if request.GET.get("format") == "json":
        return JsonResponse(data=serializer.data)

    return render(request, "elections/politic.html", context=serializer.data)


def home(request, state=None):
    return render(request, "elections/home.html", {})
