import csv
from pathlib import Path


MAPPING_PATH = Path(__file__).parent / "mapping"


def load_mapping(filename, convert_int=True, key_column="codigo", value_column="descricao"):
    result = []
    with (MAPPING_PATH / filename).open() as fobj:
        if convert_int:
            for row in csv.DictReader(fobj):
                data = (int(row[key_column]), row[value_column])
                if data not in result:
                    result.append(data)
        else:
            for row in csv.DictReader(fobj):
                data = (row[key_column], row[value_column])
                if data not in result:
                    result.append(data)
    return result


BEM_DECLARADO_TIPO = load_mapping("bem-declarado-tipo.csv", convert_int=True)
