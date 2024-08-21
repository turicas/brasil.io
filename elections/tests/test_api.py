import pytest
from django.urls import reverse
from model_bakery import baker

from elections.models import Candidacy


@pytest.mark.django_db
class TestDetailCandidacy:
    url_name = "election:candidacy_detail"
    http_user_agent = "test"

    def test_get_detail_candidacy(self, client, settings):
        candidacy = baker.make(Candidacy, _fill_optional=True)

        url = reverse(self.url_name, kwargs={"pk": candidacy.pk})
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {}

        assert resp.status_code == 200
        assert resp.json() == expected_data


@pytest.mark.django_db
class TestListCandidacy:
    url_name = "election:candidacy_list"
    http_user_agent = "test"

    def test_get_list_candidacy(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        url = reverse(self.url_name)
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "id": candidacy_1.id,
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
            },
            {
                "id": candidacy_2.id,
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["results"] == expected_data

    def test_get_list_candidacy_filter_by_year(self, client, settings):
        baker.make(Candidacy, ano=2024, _quantity=2, _fill_optional=True)
        candidacies_2023 = baker.make(Candidacy, ano=2023, _quantity=2, _fill_optional=True)

        url = reverse(self.url_name) + "?year=2023"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "id": candidacies_2023[0].id,
                "name": candidacies_2023[0].nome,
                "year": candidacies_2023[0].ano,
            },
            {
                "id": candidacies_2023[1].id,
                "name": candidacies_2023[1].nome,
                "year": candidacies_2023[1].ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["results"] == expected_data

    def test_get_list_candidacy_filter_by_uf(self, client, settings):
        baker.make(Candidacy, sigla_unidade_federativa="sp", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="rj",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            sigla_unidade_federativa="rj",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?uf=rj"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "id": candidacies_2023_rj_1.id,
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "id": candidacies_2023_rj_2.id,
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["results"] == expected_data

    def test_get_list_candidacy_paginate(self, client, settings):
        baker.make(Candidacy, _quantity=2, _fill_optional=True)
        candidacies_2023 = baker.make(Candidacy, _quantity=2, _fill_optional=True)

        url = reverse(self.url_name) + "?page=1&page_size=1"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "id": candidacies_2023[0].id,
                "name": candidacies_2023[0].nome,
                "year": candidacies_2023[0].ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["results"] == expected_data
