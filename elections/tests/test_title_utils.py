from elections.title_utils import candidacy_list_title


def test_candidacy_list_title():
    assert candidacy_list_title(
        ano=2024,
        cargo="vereador",
        estado="Todos",
        partido="Todos",
        q="Rio de Janeiro"
    ) == "Candidato(s) a vereador em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano=2024,
        cargo="Todos",
        estado="RJ",
        partido="PPP",
        q="Rio de Janeiro"
    ) == "Candidato(s) em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano=2024,
        cargo="Vereador",
        estado="Todos",
        partido="Todos",
        q=None,
    ) == "Candidato(s) a vereador em 2024"

    assert candidacy_list_title(
        ano=2024,
        cargo="Vereador",
        estado="RJ",
        partido="Todos",
        q=None,
    ) == "Candidato(s) a vereador em RJ em 2024"

    assert candidacy_list_title(
        ano=2024,
        cargo="Vereador",
        estado="rj",
        partido="Todos",
        q="João",
        q_type="name",
    ) == 'Candidato(s) "João" a vereador em RJ em 2024'
