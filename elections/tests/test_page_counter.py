from elections.page_counter import counter


def test_page_counter():
    assert counter(page=1, page_size=20, total=10_000) == "1-20 de 10.000"
    assert counter(page=2, page_size=20, total=18_500) == "21-40 de 18.500"
    assert counter(page=4, page_size=20, total=1_562_500) == "61-80 de 1.562.500"
