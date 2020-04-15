from brazil_data.cities import get_city_info


def test_get_info_from_city_if_correct_data():
    info = get_city_info('Nova Friburgo', 'RJ')
    assert 3303401 == info.city_ibge_code


def test_no_city_if_unexisting_state():
    info = get_city_info('Nova Friburgo', 'XX')
    assert info is None


def test_no_city_if_unexisting_city():
    info = get_city_info('Nova Friburgo', 'RR')
    assert info is None


def test_get_city_info_even_if_wrong_letter_cases():
    info = get_city_info('nova friburgo', 'rj')
    assert 3303401 == info.city_ibge_code
