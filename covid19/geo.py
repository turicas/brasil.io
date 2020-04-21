from itertools import groupby

from cache_memoize import cache_memoize

from core.util import http_get_json


def download_city_geojson():
    url = "https://data.brasil.io/dataset/shapefiles-brasil/0.01/BR-municipios.geojson"
    data = http_get_json(url, 5)
    return data


@cache_memoize(timeout=None)
def city_geojson():
    geojson = download_city_geojson()
    feature_id_func = lambda feature: feature["properties"]["CD_GEOCMU"]
    geojson["features"].sort(key=feature_id_func)
    for feature_id, features in groupby(geojson["features"], key=feature_id_func):
        features = list(features)
        for feature in features:
            feature["id"] = int(feature_id)
            feature["properties"] = {}
        if len(features) > 1:
            raise RuntimeError(f"Duplicate feature id {feature_id}")
    return geojson
