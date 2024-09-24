import pytest
from django.urls import reverse
from model_bakery import baker

from elections.models import (
    Candidacy,
    CandidacyMetadata,
    CandidacySocialNetwork,
    SocialNetworkMetadata,
)


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

        self.facebook = baker.make(SocialNetworkMetadata, name="facebook")
        self.tiktok = baker.make(SocialNetworkMetadata, name="tiktok")

    def test_get_detail_candidacy(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01-12",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            municipio_slug="rio-de-janeiro",
            _fill_optional=True
        )
        candidacy_facebook = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            social_network_metadata=self.facebook,
            username="@deputado-fb",
        )
        candidacy_tiktok = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            social_network_metadata=self.tiktok,
            username="@deputado-tiktok",
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "municipio": candidacy.municipio_slug,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {"data_nascimento": "12/01/1981", "info_list": candidacy.info_list}
        expected_social_networks = {
            "label": "Mídias Sociais",
            "type": "social_networks",
            "collapsed": True,
            "value": [
                {
                    "label": candidacy_facebook.username,
                    "icon": candidacy_facebook.social_network_metadata.icon,
                    "link": candidacy_facebook.link,
                },
                {
                    "label": candidacy_tiktok.username,
                    "icon": candidacy_tiktok.social_network_metadata.icon,
                    "link": candidacy_tiktok.link,
                },
            ],
        }
        assert resp.status_code == 200
        assert resp.json()["item"]["data_nascimento"] == expected_data["data_nascimento"]
        assert resp.json()["info_list"] == expected_data["info_list"]
        assert resp.json()["details_list"][0] == expected_social_networks

    def test_get_detail_candidacy_wrong_data_nascimento_format_json(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            municipio_slug="rio-de-janeiro",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "municipio": candidacy.municipio_slug,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {"data_nascimento": None}

        assert resp.status_code == 200
        assert resp.json()["item"]["data_nascimento"] == expected_data["data_nascimento"]

    def test_get_detail_candidacy_wrong_data_nascimento_format_html(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            municipio_slug="rio-de-janeiro",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano,
                "uf": candidacy.sigla_unidade_federativa,
                "municipio": candidacy.municipio_slug,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        )
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {"data_nascimento": None}

        assert resp.status_code == 200
        assert resp.context["data"]["item"]["data_nascimento"] == expected_data["data_nascimento"]
        assert resp.context["data"]["metadata"] == self.metadata
        assert resp.context["data"]["info_list"] == candidacy.info_list

    def test_get_detail_candidacy_not_found(self, client, settings):
        candidacy = baker.make(
            Candidacy,
            data_nascimento="1981-01",
            ano="2024",
            cargo_slug="deputado",
            nome_urna_slug="joao-graca",
            sigla_unidade_federativa="rj",
            municipio_slug="rio-de-janeiro",
            _fill_optional=True
        )

        url = reverse(
            self.url_name,
            kwargs={
                "ano": candidacy.ano + "1",
                "uf": candidacy.sigla_unidade_federativa,
                "municipio": candidacy.municipio_slug,
                "cargo": candidacy.cargo_slug,
                "nome": candidacy.nome_urna_slug,
            }
        ) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")

        assert resp.status_code == 404



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

    def test_get_list_candidacy_json(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name) + "?format=json"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_1.municipio_slug}/"
                    f"{candidacy_1.cargo_slug}/"
                    f"{candidacy_1.nome_urna_slug}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
                "cargo": candidacy_1.cargo,
                "municipio": candidacy_1.municipio,
                "uf": candidacy_1.sigla_unidade_federativa,
                "numero_urna": candidacy_1.numero_urna,
                "sigla_partido": candidacy_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_2.municipio_slug}/"
                    f"{candidacy_2.cargo_slug}/"
                    f"{candidacy_2.nome_urna_slug}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
                "cargo": candidacy_2.cargo,
                "municipio": candidacy_2.municipio,
                "uf": candidacy_2.sigla_unidade_federativa,
                "numero_urna": candidacy_2.numero_urna,
                "sigla_partido": candidacy_2.sigla_partido,
            },
        ]

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data

    def test_get_list_candidacy_html(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name)
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_1.municipio_slug}/"
                    f"{candidacy_1.cargo_slug}/"
                    f"{candidacy_1.nome_urna_slug}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
                "cargo": candidacy_1.cargo,
                "municipio": candidacy_1.municipio,
                "uf": candidacy_1.sigla_unidade_federativa,
                "numero_urna": candidacy_1.numero_urna,
                "sigla_partido": candidacy_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_2.municipio_slug}/"
                    f"{candidacy_2.cargo_slug}/"
                    f"{candidacy_2.nome_urna_slug}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
                "cargo": candidacy_2.cargo,
                "municipio": candidacy_2.municipio,
                "uf": candidacy_2.sigla_unidade_federativa,
                "numero_urna": candidacy_2.numero_urna,
                "sigla_partido": candidacy_2.sigla_partido,
            },
        ]

        assert resp.status_code == 200
        assert resp.context["data"]["items"] == expected_data
        assert resp.context["data"]["metadata"] == self.metadata

    def test_get_list_candidacy_when_filter_is_todos_json(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name) + "?format=json&partido=Todos&cargo=Todos&uf=Todos"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_1.municipio_slug}/"
                    f"{candidacy_1.cargo_slug}/"
                    f"{candidacy_1.nome_urna_slug}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
                "cargo": candidacy_1.cargo,
                "municipio": candidacy_1.municipio,
                "uf": candidacy_1.sigla_unidade_federativa,
                "numero_urna": candidacy_1.numero_urna,
                "sigla_partido": candidacy_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_2.municipio_slug}/"
                    f"{candidacy_2.cargo_slug}/"
                    f"{candidacy_2.nome_urna_slug}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
                "cargo": candidacy_2.cargo,
                "municipio": candidacy_2.municipio,
                "uf": candidacy_2.sigla_unidade_federativa,
                "numero_urna": candidacy_2.numero_urna,
                "sigla_partido": candidacy_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em 2024"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_when_filter_is_todos_html(self, client, settings):
        candidacy_1 = baker.make(Candidacy, ano=2024, _fill_optional=True)
        candidacy_2 = baker.make(Candidacy, ano=2023, _fill_optional=True)

        baker.make(CandidacyMetadata)  # older metadata
        baker.make(CandidacyMetadata, data=self.metadata)

        url = reverse(self.url_name) + "?partido=Todos&cargo=Todos&uf=Todos"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_1.ano}/"
                    f"{candidacy_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_1.municipio_slug}/"
                    f"{candidacy_1.cargo_slug}/"
                    f"{candidacy_1.nome_urna_slug}/"
                ),
                "name": candidacy_1.nome,
                "year": candidacy_1.ano,
                "cargo": candidacy_1.cargo,
                "municipio": candidacy_1.municipio,
                "uf": candidacy_1.sigla_unidade_federativa,
                "numero_urna": candidacy_1.numero_urna,
                "sigla_partido": candidacy_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacy_2.ano}/"
                    f"{candidacy_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacy_2.municipio_slug}/"
                    f"{candidacy_2.cargo_slug}/"
                    f"{candidacy_2.nome_urna_slug}/"
                ),
                "name": candidacy_2.nome,
                "year": candidacy_2.ano,
                "cargo": candidacy_2.cargo,
                "municipio": candidacy_2.municipio,
                "uf": candidacy_2.sigla_unidade_federativa,
                "numero_urna": candidacy_2.numero_urna,
                "sigla_partido": candidacy_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em 2024"

        assert resp.status_code == 200
        assert resp.context["data"]["items"] == expected_data
        assert resp.context["data"]["metadata"] == self.metadata
        assert resp.context["data"]["title"] == expected_title

    def test_get_list_candidacy_filter_by_year_json(self, client, settings):
        baker.make(Candidacy, ano=2022, _quantity=2, _fill_optional=True)
        candidacies_2024 = baker.make(Candidacy, ano=2024, _quantity=2, _fill_optional=True)

        url = reverse(self.url_name) + "?format=json&ano=2023"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024[0].ano}/"
                    f"{candidacies_2024[0].sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024[0].municipio_slug}/"
                    f"{candidacies_2024[0].cargo_slug}/"
                    f"{candidacies_2024[0].nome_urna_slug}/"
                ),
                "name": candidacies_2024[0].nome,
                "year": candidacies_2024[0].ano,
                "cargo": candidacies_2024[0].cargo,
                "municipio": candidacies_2024[0].municipio,
                "uf": candidacies_2024[0].sigla_unidade_federativa,
                "numero_urna": candidacies_2024[0].numero_urna,
                "sigla_partido": candidacies_2024[0].sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024[1].ano}/"
                    f"{candidacies_2024[1].sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024[1].municipio_slug}/"
                    f"{candidacies_2024[1].cargo_slug}/"
                    f"{candidacies_2024[1].nome_urna_slug}/"
                ),
                "name": candidacies_2024[1].nome,
                "year": candidacies_2024[1].ano,
                "cargo": candidacies_2024[1].cargo,
                "municipio": candidacies_2024[1].municipio,
                "uf": candidacies_2024[1].sigla_unidade_federativa,
                "numero_urna": candidacies_2024[1].numero_urna,
                "sigla_partido": candidacies_2024[1].sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em 2024"
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "Todos",
            "t": "cidade",
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_year_html(self, client, settings):
        baker.make(Candidacy, ano=2023, _quantity=2, _fill_optional=True)
        candidacies_2024 = baker.make(Candidacy, ano=2024, _quantity=2, _fill_optional=True)

        url = reverse(self.url_name) + "?ano=2023"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024[0].ano}/"
                    f"{candidacies_2024[0].sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024[0].municipio_slug}/"
                    f"{candidacies_2024[0].cargo_slug}/"
                    f"{candidacies_2024[0].nome_urna_slug}/"
                ),
                "name": candidacies_2024[0].nome,
                "year": candidacies_2024[0].ano,
                "cargo": candidacies_2024[0].cargo,
                "municipio": candidacies_2024[0].municipio,
                "uf": candidacies_2024[0].sigla_unidade_federativa,
                "numero_urna": candidacies_2024[0].numero_urna,
                "sigla_partido": candidacies_2024[0].sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024[1].ano}/"
                    f"{candidacies_2024[1].sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024[1].municipio_slug}/"
                    f"{candidacies_2024[1].cargo_slug}/"
                    f"{candidacies_2024[1].nome_urna_slug}/"
                ),
                "name": candidacies_2024[1].nome,
                "year": candidacies_2024[1].ano,
                "cargo": candidacies_2024[1].cargo,
                "municipio": candidacies_2024[1].municipio,
                "uf": candidacies_2024[1].sigla_unidade_federativa,
                "numero_urna": candidacies_2024[1].numero_urna,
                "sigla_partido": candidacies_2024[1].sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em 2024"
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "Todos",
            "t": "cidade",
        }

        assert resp.status_code == 200
        assert resp.context["data"]["items"] == expected_data
        assert resp.context["data"]["filters"] == expected_filters
        assert resp.context["data"]["title"] == expected_title
        assert resp.context["data"]["metadata"] == self.metadata

    def test_get_list_candidacy_filter_by_uf(
        self, client, settings
    ):
        baker.make(Candidacy, ano=2018, sigla_unidade_federativa="sp", _quantity=2, _fill_optional=True)
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="RJ",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="RJ",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&uf=RJ"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) no RJ em 2024"
        expected_filters = {
            "cargo": "Todos",
            "uf": "RJ",
            "partido": "Todos",
            "t": "cidade",
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_cargo_slug(self, client, settings):
        baker.make(Candidacy, ano=2024, cargo_slug="deputado-estadual", _quantity=2, _fill_optional=True)
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            cargo_slug="senado",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            cargo_slug="senado",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&cargo=senado"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) ao senado em 2024"
        expected_filters = {
            "cargo": "senado",
            "uf": "Todos",
            "partido": "Todos",
            "t": "cidade",
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_partido(self, client, settings):
        baker.make(Candidacy, ano=2024, sigla_partido="aaa", _quantity=2, _fill_optional=True)
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_partido="ppp",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            sigla_partido="PPP",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&partido=ppp"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "ppp",
            "t": "cidade",
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters

    def test_get_list_candidacy_filter_by_name(self, client, settings):
        baker.make(Candidacy, ano=2024, nome="Paulo Silva", _quantity=2, _fill_optional=True)
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            nome_urna="João do 42",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            nome_urna="João Graça",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=joao&t=nome"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]

        expected_title = 'Candidato(s) "joao" em 2024'
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "Todos",
            "q": "joao",
            "t": "nome"
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_city(self, client, settings):
        # TODO: checar campo municipio
        baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="pe",
            municipio="Recife",
            _quantity=2,
            _fill_optional=True
        )
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="rj",
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="rj",
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=Rio de Janeiro-RJ&t=cidade"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em Rio de Janeiro (RJ) em 2024"
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "Todos",
            "q": "Rio de Janeiro-RJ",
            "t": "cidade"
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_filter_by_city_default_field(self, client, settings):
        # TODO: checar campo municipio
        baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="PE",
            municipio="Recife",
            _quantity=2,
            _fill_optional=True,
        )
        candidacies_2024_rj_1 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="rj",
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )
        candidacies_2024_rj_2 = baker.make(
            Candidacy,
            ano=2024,
            sigla_unidade_federativa="RJ",
            municipio="Rio de Janeiro",
            _fill_optional=True,
        )

        url = reverse(self.url_name) + "?format=json&q=Rio de Janeiro-RJ"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_1.ano}/"
                    f"{candidacies_2024_rj_1.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_1.municipio_slug}/"
                    f"{candidacies_2024_rj_1.cargo_slug}/"
                    f"{candidacies_2024_rj_1.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_1.nome,
                "year": candidacies_2024_rj_1.ano,
                "cargo": candidacies_2024_rj_1.cargo,
                "municipio": candidacies_2024_rj_1.municipio,
                "uf": candidacies_2024_rj_1.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_1.numero_urna,
                "sigla_partido": candidacies_2024_rj_1.sigla_partido,
            },
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024_rj_2.ano}/"
                    f"{candidacies_2024_rj_2.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024_rj_2.municipio_slug}/"
                    f"{candidacies_2024_rj_2.cargo_slug}/"
                    f"{candidacies_2024_rj_2.nome_urna_slug}/"
                ),
                "name": candidacies_2024_rj_2.nome,
                "year": candidacies_2024_rj_2.ano,
                "cargo": candidacies_2024_rj_2.cargo,
                "municipio": candidacies_2024_rj_2.municipio,
                "uf": candidacies_2024_rj_2.sigla_unidade_federativa,
                "numero_urna": candidacies_2024_rj_2.numero_urna,
                "sigla_partido": candidacies_2024_rj_2.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em Rio de Janeiro (RJ) em 2024"
        expected_filters = {
            "cargo": "Todos",
            "uf": "Todos",
            "partido": "Todos",
            "q": "Rio de Janeiro-RJ",
            "t": "cidade"
        }

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["filters"] == expected_filters
        assert resp.json()["title"] == expected_title

    def test_get_list_candidacy_paginate(self, client, settings):
        baker.make(Candidacy, ano=2024, _quantity=2, _fill_optional=True)
        candidacies_2024 = baker.make(Candidacy, ano=2024, _fill_optional=True)

        url = reverse(self.url_name) + "?format=json&page=1&page_size=1"
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = [
            {
                "path": (
                    "/eleicoes/"
                    f"{candidacies_2024.ano}/"
                    f"{candidacies_2024.sigla_unidade_federativa.lower()}/"
                    f"{candidacies_2024.municipio_slug}/"
                    f"{candidacies_2024.cargo_slug}/"
                    f"{candidacies_2024.nome_urna_slug}/"
                ),
                "name": candidacies_2024.nome,
                "year": candidacies_2024.ano,
                "cargo": candidacies_2024.cargo,
                "municipio": candidacies_2024.municipio,
                "uf": candidacies_2024.sigla_unidade_federativa,
                "numero_urna": candidacies_2024.numero_urna,
                "sigla_partido": candidacies_2024.sigla_partido,
            },
        ]
        expected_title = "Candidato(s) em 2024"

        assert resp.status_code == 200
        assert resp.json()["items"] == expected_data
        assert resp.json()["title"] == expected_title
