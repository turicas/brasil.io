def candidacy_list_title(
    *,
    ano="todos",
    cargo="todos",
    uf="todos",
    q=None,
    t="city",
    **kwargs
):
    if cargo.lower() == "todos":
        cargo = None
    if uf.lower() == "todos":
        uf = None

    title = "Candidato(s)"

    if q is not None and t == "name":
        title += f' "{q}"'

    if cargo:
        preposicao = "a"
        if cargo.lower() in ("senado"):
            preposicao = "ao"
        title += f" {preposicao} {cargo.lower()}"

    if q is not None and t == "city":
        title += f" em {q}"

    if uf is not None and not (q is not None and t == "city"):
        title += f" em {uf.upper()}"

    if ano is not None and ano.isdigit():
        title += f" em {ano}"
    elif (isinstance(ano, str) and ano.lower() == "todos") or ano is None:
        title += " em todos os anos"

    return title
