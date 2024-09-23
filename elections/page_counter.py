def counter(*, page, page_size, total):
    return f"{(page - 1) * page_size + 1}-{page * page_size} de {total:_d}".replace("_", ".")
