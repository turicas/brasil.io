from elections.title_utils import candidacy_list_title


def test_candidacy_list_title():
    assert candidacy_list_title(
        ano="2024",
        cargo="vereador",
        uf="Todos",
        partido="todos",
        q="Rio de Janeiro"
    ) == "Candidato(s) a vereador em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Todos",
        uf="RJ",
        partido="todos",
        q="Rio de Janeiro",
        t="cidade",
    ) == "Candidato(s) em Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="Todos",
        partido="todos",
        q=None,
    ) == "Candidato(s) a vereador em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="Rio de Janeiro",
        partido="todos",
        q=None,
    ) == "Candidato(s) a vereador no Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Senado",
        uf="Rio de Janeiro",
        partido="todos",
        q=None,
    ) == "Candidato(s) ao senado no Rio de Janeiro em 2024"

    assert candidacy_list_title(
        ano="2024",
        cargo="Vereador",
        uf="São Paulo",
        partido="todos",
        q="João",
        t="name",
    ) == 'Candidato(s) "João" a vereador em São Paulo em 2024'

    assert candidacy_list_title(
        ano="2024",
        cargo="Todos",
        uf="Todos",
        partido="todos",
        q=None,
    ) == 'Candidato(s) em 2024'

    assert candidacy_list_title(
        ano="todos",
        cargo="Todos",
        uf="Todos",
        partido="todos",
        q=None,
    ) == 'Candidato(s) em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Todos",
        partido="todos",
        q=None,
    ) == 'Candidato(s) em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Minas Gerais",
        partido="todos",
        q=None,
    ) == 'Candidato(s) em Minas Gerais em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Espírito Santo",
        partido="todos",
        q=None,
    ) == 'Candidato(s) no Espírito Santo em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Espírito Santo",
        partido="PPP",
        q=None,
    ) == 'Candidato(s) do "PPP" no Espírito Santo em todos os anos'

    assert candidacy_list_title(
        ano=None,
        cargo="Todos",
        uf="Espírito Santo",
        partido="PPP",
        q=None,
        ano_inicio="2014",
    ) == 'Candidato(s) do "PPP" no Espírito Santo desde 2014'
