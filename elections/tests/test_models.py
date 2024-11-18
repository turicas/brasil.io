from datetime import date
from uuid import uuid4

import pytest
from freezegun import freeze_time
from model_bakery import baker

from elections.models import (
    BemDeclarado,
    Candidacy,
    CandidacySocialNetwork,
    SocialNetworkMetadata,
)


@pytest.mark.django_db
class TestCandidacy:
    def test_get_first_year(self):
        baker.make(Candidacy, ano=2018)
        baker.make(Candidacy, ano=2022)
        baker.make(Candidacy, ano=2014)

        assert Candidacy.first_year() == 2014

    @freeze_time("2024-09-17")
    def test_candidacy_detail_list(self):
        candidacy = baker.make(
            Candidacy,
            composicao_legenda="PRB / PTN / PHS / PPL",
            situacao="DEFERIDO",
            nome="Nome Completo",
            nome_urna="Nome Urna",
            etnia="ETNIA",
            genero="GENERO",
            data_nascimento=date(1999, 1, 1),
            grau_instrucao="GRAU INSTRUÇÃO",
            ocupacao="OCUPACAO",
            estado_civil="ESTADO CIVIL",
            ano=2018
        )
        expected = [
            {"label": "Coligação", "value": "PRB, PTN, PHS e PPL"},
            {"label": "Situação candidatura", "value": candidacy.situacao, "type": "tag"},
            {"label": "Nome completo", "value": candidacy.nome},
            {"label": "Nome urna", "value": candidacy.nome_urna},
            {"label": "Nascimento", "value": "01/01/1999 (25 anos)"},
            {"label": "Cor/Raça", "value": candidacy.etnia},
            {"label": "Gênero", "value": candidacy.genero},
            {"label": "Estado civil", "value": candidacy.estado_civil},
            {"label": "Grau de instrução", "value": candidacy.grau_instrucao},
            {"label": "Profissão/Ocupação", "value": candidacy.ocupacao},
        ]

        assert candidacy.info_list == expected

    @freeze_time("2024-09-17")
    def test_candidacy_detail_list_different_values(self):
        candidacy = baker.make(
            Candidacy,
            composicao_legenda="PRB",
            situacao="DEFERIDO",
            nome="Nome Completo",
            nome_urna="Nome Urna",
            etnia="ETNIA",
            genero="GENERO",
            data_nascimento=None,
            grau_instrucao="GRAU INSTRUÇÃO",
            ocupacao="OCUPACAO",
            estado_civil="ESTADO CIVIL",
            ano=2018
        )
        expected = [
            {"label": "Coligação", "value": "PRB"},
            {"label": "Situação candidatura", "value": candidacy.situacao, "type": "tag"},
            {"label": "Nome completo", "value": candidacy.nome},
            {"label": "Nome urna", "value": candidacy.nome_urna},
            {"label": "Nascimento", "value": "Não informado"},
            {"label": "Cor/Raça", "value": candidacy.etnia},
            {"label": "Gênero", "value": candidacy.genero},
            {"label": "Estado civil", "value": candidacy.estado_civil},
            {"label": "Grau de instrução", "value": candidacy.grau_instrucao},
            {"label": "Profissão/Ocupação", "value": candidacy.ocupacao},
        ]

        assert candidacy.info_list == expected


@pytest.mark.django_db
class TestCandidacySocialNetwork:
    def test_link(self):
        facebook = baker.make(
            SocialNetworkMetadata,
            name="facebook",
            url_prefix="https://facebook.com",
        )
        candidacy_facebook = baker.make(
            CandidacySocialNetwork,
            username="candidato-fb",
            social_network_metadata=facebook,
        )

        assert candidacy_facebook.link == "https://facebook.com/candidato-fb"

    def test_list_social_networks(self):
        candidacy = baker.make(Candidacy)
        facebook = baker.make(
            SocialNetworkMetadata,
            name="facebook",
            url_prefix="https://facebook.com",
        )
        tiktok = baker.make(
            SocialNetworkMetadata,
            name="tiktok",
            url_prefix="https://tiktok.com",
        )
        candidacy_facebook = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-fb",
            social_network_metadata=facebook,
        )
        candidacy_tiktok = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-tk",
            social_network_metadata=tiktok,
        )

        social_networks = candidacy.social_networks_list()
        expected = [
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
        ]

        assert social_networks == expected

    def test_list_social_networks_order_by_position(self):
        candidacy = baker.make(Candidacy)
        facebook = baker.make(
            SocialNetworkMetadata,
            name="facebook",
            url_prefix="https://facebook.com",
        )
        tiktok = baker.make(
            SocialNetworkMetadata,
            name="tiktok",
            url_prefix="https://tiktok.com",
        )
        candidacy_facebook = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-fb",
            position=2,
            social_network_metadata=facebook,
        )
        candidacy_tiktok_1 = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-tk-1",
            position=1,
            social_network_metadata=tiktok,
        )
        candidacy_tiktok_2 = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-tk-2",
            position=None,
            social_network_metadata=tiktok,
        )
        candidacy_tiktok_3 = baker.make(
            CandidacySocialNetwork,
            candidacy=candidacy,
            username="candidato-tk-3",
            position=None,
            social_network_metadata=tiktok,
        )

        social_networks = candidacy.social_networks_list()
        expected = [
            {
                "label": candidacy_tiktok_1.username,
                "icon": candidacy_tiktok_1.social_network_metadata.icon,
                "link": candidacy_tiktok_1.link,
            },
            {
                "label": candidacy_facebook.username,
                "icon": candidacy_facebook.social_network_metadata.icon,
                "link": candidacy_facebook.link,
            },
            {
                "label": candidacy_tiktok_2.username,
                "icon": candidacy_tiktok_2.social_network_metadata.icon,
                "link": candidacy_tiktok_2.link,
            },
            {
                "label": candidacy_tiktok_3.username,
                "icon": candidacy_tiktok_3.social_network_metadata.icon,
                "link": candidacy_tiktok_3.link,
            },
        ]

        assert social_networks == expected


@pytest.mark.django_db
class TestBemDeclarado:
    def test_bens_declarados_list(self):
        person_uuid = str(uuid4())
        candidacy = baker.make(Candidacy, person_uuid=person_uuid)

        bem_declarado_1 = baker.make(BemDeclarado, person_uuid=person_uuid, valor=100_000)
        bem_declarado_2 = baker.make(BemDeclarado, person_uuid=person_uuid, valor=200_000)
        bem_declarado_3 = baker.make(BemDeclarado, person_uuid=person_uuid, valor=300_000)

        bens_declarados, total = candidacy.bens_declarados()
        expected_values = [
            {
                "label": bem_declarado_3.get_tipo_display(),
                "description": bem_declarado_3.descricao,
                "value": bem_declarado_3.valor,
            },
            {
                "label": bem_declarado_2.get_tipo_display(),
                "description": bem_declarado_2.descricao,
                "value": bem_declarado_2.valor,
            },
            {
                "label": bem_declarado_1.get_tipo_display(),
                "description": bem_declarado_1.descricao,
                "value": bem_declarado_1.valor,
            },
        ]
        expected_total = 600_000

        assert bens_declarados == expected_values
        assert total == expected_total
