import pytest
from freezegun import freeze_time
from model_bakery import baker

from elections.models import Candidacy, CandidacySocialNetwork, SocialNetworkMetadata


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
            data_nascimento="1999-01-01",
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
