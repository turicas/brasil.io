import json
import gzip
from itertools import groupby
from pathlib import Path
from urllib.request import Request, urlopen

from django.core.cache import cache


def http_get_compressed(url):
    request = Request(url, headers={"Accept-Encoding": "gzip, deflate"})
    response = urlopen(request)
    encoding = response.info().get("Content-Encoding")
    response_data = response.read()
    if encoding in ("deflate", None):
        data = response_data
    elif encoding == "gzip":
        data = gzip.decompress(response_data)
    else:
        raise RuntimeError(f"Unknown encoding: {repr(encoding)}")
    return data


def download_city_geojson():
    url = "https://data.brasil.io/dataset/shapefiles-brasil/0.01/BR-municipios.geojson"
    response_data = http_get_compressed(url)
    data = json.loads(response_data)
    return data


def city_geojson():
    cache_key = "geojson:BR:city"
    data = cache.get(cache_key, None)
    if data is None:
        data = download_city_geojson()
        cache.set(cache_key, data)

    feature_id_func = lambda feature: feature["properties"]["CD_GEOCMU"]
    data["features"].sort(key=feature_id_func)
    for feature_id, features in groupby(data["features"], key=feature_id_func):
        features = list(features)
        for feature in features:
            feature["id"] = int(feature_id)
            feature["properties"] = {}
        if len(features) > 1:
            raise RuntimeError(f"Duplicate feature id {feature_id}")
    return data
