from itertools import groupby

from cache_memoize import cache_memoize

from core.util import http_get_json


@cache_memoize(timeout=None)
def download_state_geojson(tolerance):
    url = f"https://data.brasil.io/dataset/shapefiles-brasil/{tolerance}/BR-UF.geojson"
    data = http_get_json(url, 5)
    return data


@cache_memoize(timeout=None)
def download_city_geojson(tolerance):
    url = f"https://data.brasil.io/dataset/shapefiles-brasil/{tolerance}/BR-municipios.geojson"
    data = http_get_json(url, 5)
    return data


@cache_memoize(timeout=None)
def state_geojson(high_fidelity=False):
    tolerance = 0.01 if not high_fidelity else 0.001
    geojson = download_state_geojson(tolerance)
    return geojson


@cache_memoize(timeout=None)
def city_geojson(high_fidelity=False):
    tolerance = 0.01 if not high_fidelity else 0.001
    geojson = download_city_geojson(tolerance)
    feature_id_func = lambda feature: feature["properties"]["CD_GEOCMU"]  # noqa
    geojson["features"].sort(key=feature_id_func)
    for feature_id, features in groupby(geojson["features"], key=feature_id_func):
        features = list(features)
        for feature in features:
            feature["id"] = int(feature_id)
            feature["properties"] = {}
        if len(features) > 1:
            raise RuntimeError(f"Duplicate feature id {feature_id}")
    return geojson
