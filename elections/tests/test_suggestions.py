from unittest import mock

from elections.suggestions import create_search_suggestions


@mock.patch("elections.suggestions.random.shuffle")
def test_suggestions(m_shuffle):
    m_shuffle.side_effect = lambda x: x

    cargos = ("vereador", "prefeito",)
    cities = ("Rio de Janeiro", "Manaus", "Recife", "Brasil")
    search_suggestions = create_search_suggestions(cargos=cargos, cities=cities)

    expected = [
        {
            "title": "Vereador no Rio de Janeiro (RJ)",
            "path": "/eleicoes/2024/?cargo=Vereador&q=Rio de Janeiro",
        },
        {
            "title": "Vereador em Manaus (AM)",
            "path": "/eleicoes/2024/?cargo=Vereador&q=Manaus",
        },
        {
            "title": "Vereador no Recife (PE)",
            "path": "/eleicoes/2024/?cargo=Vereador&q=Recife",
        },
        {
            "title": "Vereador no Brasil",
            "path": "/eleicoes/2024/?cargo=Vereador",
        },
        {
            "title": "Prefeito no Rio de Janeiro (RJ)",
            "path": "/eleicoes/2024/?cargo=Prefeito&q=Rio de Janeiro",
        },
        {
            "title": "Prefeito em Manaus (AM)",
            "path": "/eleicoes/2024/?cargo=Prefeito&q=Manaus",
        },
        {
            "title": "Prefeito no Recife (PE)",
            "path": "/eleicoes/2024/?cargo=Prefeito&q=Recife",
        },
        {
            "title": "Prefeito no Brasil",
            "path": "/eleicoes/2024/?cargo=Prefeito",
        },
    ]

    assert search_suggestions == expected
    m_shuffle.assert_called_once()
