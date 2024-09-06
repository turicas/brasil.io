from elections.title_utils import candidacy_list_title


def test_candidacy_list_title():
    assert candidacy_list_title(
        ano="2024",
        cargo="vereador",
        uf="Todos",
        q="Rio de Janeiro"
    ) == "Candidato(s) a vereador em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Todos",
        uf="RJ",
        q="Rio de Janeiro"
    ) == "Candidato(s) em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="Todos",
        q=None,
    ) == "Candidato(s) a vereador em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="RJ",
        q=None,
    ) == "Candidato(s) a vereador em RJ em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Senado",
        uf="RJ",
        q=None,
    ) == "Candidato(s) ao senado em RJ em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="rj",
        q="João",
        t="name",
    ) == 'Candidato(s) "João" a vereador em RJ em 2024'

    assert candidacy_list_title(
        ano="2024",
        cargo="Todos",
        uf="Todos",
        q=None,
    ) == 'Candidato(s) em 2024'

    assert candidacy_list_title(
        ano="todos",
        cargo="Todos",
        uf="Todos",
        q=None,
    ) == 'Candidato(s) em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Todos",
        q=None,
    ) == 'Candidato(s) em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="rj",
        q=None,
    ) == 'Candidato(s) em RJ em todos os anos'
