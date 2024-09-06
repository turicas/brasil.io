def candidacy_list_title(ano, cargo, estado, partido, q, q_type="city"):
    if cargo.lower() == "todos":
        cargo = None
    if estado.lower() == "todos":
        estado = None
    if partido == "todos":
        partido = None

    title = "Candidato(s)"

    if q is not None and q_type == "name":
        title += f' "{q}"'

    if cargo:
        title += f" a {cargo.lower()}"

    if q is not None and q_type == "city":
        title += f" em {q}"

    if estado is not None and not (q is not None and q_type == "city"):
        title += f" em {estado.upper()}"

    if ano is not None:
        title += f" em {ano}"

    return title
