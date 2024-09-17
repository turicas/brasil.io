import pytest
from freezegun import freeze_time
from model_bakery import baker

from elections.models import Candidacy


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
            {"label": "Situação candidatura", "value": candidacy.situacao},
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
