import pytest
from django.urls import reverse
from django.utils.text import slugify
from model_bakery import baker

from elections.models import Candidacy, CandidacyMetadata


@pytest.mark.django_db
class TestDetailCandidacyView:
    url_name = "elections:candidacy_detail"
    http_user_agent = "test"

    def setup_method(self):
        self.metadata = {
            "2024": {
                "cargo":["Todos", "Prefeito", "Vereador", "Vice-Prefeito",],
                "partido": ["Todos", "AAA", "BBB", "CCC"],
                "estado": ["Todos", "Rio de Janeiro", "São Paulo", "Minas Gerais"],
            }
        }
        baker.make(CandidacyMetadata, data=self.metadata)

    def test_get_detail_candidacy(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01-12",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {"data_nascimento": "12/01/1981"}

        assert resp.status_code == 200
        assert resp.json()["item"]["data_nascimento"] == expected_data["data_nascimento"]

    def test_get_detail_candidacy_wrong_data_nascimento_format(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {"data_nascimento": None}

        assert resp.status_code == 200
        assert resp.json()["item"]["data_nascimento"] == expected_data["data_nascimento"]
        assert resp.json()["metadata"] == self.metadata

    def test_get_detail_candidacy_not_found(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano + "1",
                "uf": candidacy.sigla_unidade_federativa,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")

        assert resp.status_code == 404

    def test_get_detail_candidacy_return_filter_parameters(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json&ano=2024&partido=Todos&cargo=senador"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")

        assert resp.status_code == 200
        assert resp.json()["metadata"] == self.metadata


@pytest.mark.django_db
class TestListCandidacy:
    url_name = "elections:candidacy_list"
    http_user_agent = "test"

    def setup_method(self):
        self.metadata = {
            "2024": {
                "cargo":["Todos", "Prefeito", "Vereador", "Vice-Prefeito",],
                "partido": ["Todos", "AAA", "BBB", "CCC"],
                "estado": ["Todos", "Rio de Janeiro", "São Paulo", "Minas Gerais"],
            }
        }
        baker.make(CandidacyMetadata, data=self.metadata)

    def test_get_list_candidacy(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacy_1.cargo)}/"
                    f"{slugify(candidacy_1.nome_urna)}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacy_2.cargo)}/"
                    f"{slugify(candidacy_2.nome_urna)}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["metadata"] == self.metadata

    def test_get_list_candidacy_when_filter_is_todos(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name) + "?format=json&partido=Todos&cargo=Todos&uf=Todos"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacy_1.cargo)}/"
                    f"{slugify(candidacy_1.nome_urna)}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacy_2.cargo)}/"
                    f"{slugify(candidacy_2.nome_urna)}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
            },
        ]
        expected_title = "Candidato(s) em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["metadata"] == self.metadata
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_year(self, client, settings):
        baker.make(Candidacy, ano=2024, _quantity=2, _fill_optional=True)
        candidacies_2023 = baker.make(Candidacy, ano=2023, _quantity=2, _fill_optional=True)

        url = reverse(self.url_name) + "?format=json&ano=2023"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023[0].ano}/"
                    f"{candidacies_2023[0].sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023[0].cargo)}/"
                    f"{slugify(candidacies_2023[0].nome_urna)}/"
                ),
                "name": candidacies_2023[0].nome,
                "year": candidacies_2023[0].ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023[1].ano}/"
                    f"{candidacies_2023[1].sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023[1].cargo)}/"
                    f"{slugify(candidacies_2023[1].nome_urna)}/"
                ),
                "name": candidacies_2023[1].nome,
                "year": candidacies_2023[1].ano,
            },
        ]
        expected_title = "Candidato(s) em 2023"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"ano": "2023"}
        assert resp.json()["title"] == expected_title

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

        url = reverse(self.url_name) + "?format=json&uf=rj"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]
        expected_title = "Candidato(s) em RJ em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"uf": "rj"}
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_cargo_slug(self, client, settings):
        baker.make(Candidacy, cargo_slug="deputado-estadual", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            cargo_slug="senado",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            cargo_slug="senado",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&cargo=senado"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]
        expected_title = "Candidato(s) ao senado em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"cargo": "senado"}
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_partido(self, client, settings):
        baker.make(Candidacy, sigla_partido="aaa", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_partido="ppp",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            sigla_partido="PPP",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&partido=ppp"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"partido": "ppp"}

    def test_get_list_candidacy_filter_by_name(self, client, settings):
        baker.make(Candidacy, nome="Paulo Silva", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            nome_urna="João do 42",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            nome_urna="João Graça",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=joao&t=name"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]

        expected_title = 'Candidato(s) "joao" em todos os anos'

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"q": "joao", "t": "name"}
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_city(self, client, settings):
        # TODO: checar campo municipio
        baker.make(Candidacy, municipio="Recife", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=rio&t=city"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]
        expected_title = "Candidato(s) em rio em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"q": "rio", "t": "city"}
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_city_default_field(self, client, settings):
        # TODO: checar campo municipio
        baker.make(Candidacy, municipio="Recife", _quantity=2, _fill_optional=True)
        candidacies_2023_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )
        candidacies_2023_rj_2 = baker.make(
            Candidacy,
            ano=2023,
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=rio"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_1.ano}/"
                    f"{candidacies_2023_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_1.cargo)}/"
                    f"{slugify(candidacies_2023_rj_1.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_1.nome,
                "year": candidacies_2023_rj_1.ano,
            },
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2023_rj_2.ano}/"
                    f"{candidacies_2023_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2023_rj_2.cargo)}/"
                    f"{slugify(candidacies_2023_rj_2.nome_urna)}/"
                ),
                "name": candidacies_2023_rj_2.nome,
                "year": candidacies_2023_rj_2.ano,
            },
        ]
        expected_title = "Candidato(s) em rio em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == {"q": "rio"}
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_paginate(self, client, settings):
        baker.make(Candidacy, ano=2023, _quantity=2, _fill_optional=True)
        candidacies_2024 = baker.make(Candidacy, ano=2024, _fill_optional=True)

        url = reverse(self.url_name) + "?format=json&page=1&page_size=1"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/politic/"
                    f"{candidacies_2024.ano}/"
                    f"{candidacies_2024.sigla_unidade_federativa.lower()}/"
                    f"{slugify(candidacies_2024.cargo)}/"
                    f"{slugify(candidacies_2024.nome_urna)}/"
                ),
                "name": candidacies_2024.nome,
                "year": candidacies_2024.ano,
            },
        ]
        expected_title = "Candidato(s) em todos os anos"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["title"] == expected_title
