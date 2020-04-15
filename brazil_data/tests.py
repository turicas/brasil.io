from brazil_data.cities import get_city_info, get_state_info


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


def test_get_state_info():
    info = get_state_info('SP')
    assert 35 == info.state_ibge_code
    assert 'SP' == info.state
    assert info == get_state_info('sp')
    assert getattr(info, 'city_ibge_code', None) is None


def test_no_state_if_unexisting_uf():
    info = get_state_info('XX')
    assert info is None
