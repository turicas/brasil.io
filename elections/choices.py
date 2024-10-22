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

EMPRESA_CNAE = load_mapping("empresa-cnae.csv", convert_int=False)
EMPRESA_MOTIVO_SITUACAO_CADASTRAL = load_mapping("empresa-motivo-situacao-cadastral.csv", convert_int=True)
EMPRESA_NATUREZA_JURIDICA = load_mapping("empresa-natureza-juridica.csv", convert_int=True)
EMPRESA_PORTE = load_mapping("empresa-porte.csv", convert_int=True)
EMPRESA_QUALIFICACAO_SOCIO = load_mapping("empresa-qualificacao-socio.csv", convert_int=True)
EMPRESA_SITUACAO_CADASTRAL = load_mapping("empresa-situacao-cadastral.csv", convert_int=True)
MUNICIPIO = load_mapping("municipio.csv", convert_int=True)
PAIS = load_mapping("pais.csv", convert_int=True)
