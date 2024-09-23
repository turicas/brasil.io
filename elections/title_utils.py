def candidacy_list_title(
    *,
    ano="todos",
    cargo="todos",
    uf="todos",
    partido="todos",
    q=None,
    t="cidade",
    ano_inicio=None,
    **kwargs
):

    uf_prepositions = {
        "RJ": "no",
        "BA": "na",
        "ES": "no",
        "PR": "no",
        "RS": "no",
        "CE": "no",
        "PA": "no",
        "MA": "no",
        "PB": "na",
        "AM": "no",
        "MT": "no",
        "RN": "no",
        "PI": "no",
        "DF": "no",
        "TO": "no",
        "AC": "no",
        "AM": "no",
        "SP": "em",
        "MG": "em",
        "PE": "em",
        "SE": "em",
        "AL": "em",
        "AP": "no",
        "GO": "em",
        "RO": "em",
        "MS": "no"
    }

    if cargo.lower() == "todos":
        cargo = None
    if uf.lower() == "todos":
        uf = None
    if partido.lower() == "todos":
        partido = None
    if ano and ano.lower() == "todos":
        ano = None

    title = "Candidato(s)"

    if partido is not None:
        title += f' do "{partido}"'

    if q is not None and t == "nome":
        title += f' "{q}"'

    if cargo:
        preposicao = "a"
        if cargo.lower() in ("senado"):
            preposicao = "ao"
        title += f" {preposicao} {cargo.lower()}"

    if q is not None and t == "cidade":
        try:
            city, state = q.rsplit("-", 1)
            title += f" em {city} ({state})"
        except ValueError:
            pass

    if uf is not None and not (q is not None and t == "cidade"):
        uf_preposition = uf_prepositions.get(uf, "em")
        if uf in uf_prepositions.keys():
            title += f" {uf_preposition} {uf.upper()}"

    if ano is not None and ano.isdigit():
        title += f" em {ano}"
    elif ano is None and ano_inicio is not None:
        title += f" desde {ano_inicio}"
    elif (isinstance(ano, str) and ano.lower() == "todos") or ano is None:
        title += " em todos os anos"

    return title
