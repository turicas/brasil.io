import csv
import gzip
import lzma
import io
from collections import defaultdict

from tqdm import tqdm


class CsvLazyDictWriter:
    """Write dicts to CSV without specifying the header

    Note: the dicts must have the same key-value pairs.
    """

    def __init__(self, filename, encoding='utf-8'):
        self.filename = filename
        if filename.endswith('.gz'):
            self.fobj = io.TextIOWrapper(
                gzip.GzipFile(filename, mode='w'),
                encoding=encoding,
            )
        else:
            self.fobj = open(filename, mode='w', encoding='encoding')
        self.writer = None

    def writerow(self, row):
        self.header = list(row.keys())
        self.writer = csv.DictWriter(self.fobj, fieldnames=self.header)
        self.writer.writeheader()
        # Optimization: no `if not self.writer` needed from 2nd row
        self.writerow = self.writer.writerow
        return self.writer.writerow(row)


class ExportGraph:

    def load_companies(self):
        companies = defaultdict(list)
        fobj = io.TextIOWrapper(
            lzma.open('../data/documentos-brasil/documents.csv.xz'),
            encoding='utf-8',
        )
        for row in tqdm(csv.DictReader(fobj)):
            if row['document_type'] == 'CNPJ':
                companies[int(row['document'][:8])].append(
                    # Storing as a tuple to save memory
                    (row['document'], row['name'])
                )
        self.companies = companies

    def get_company_name(self, cnpj, default):
        cnpj_prefix = cnpj[:8]
        hq_prefix = cnpj_prefix + '0001'
        branches = self.companies.get(int(cnpj_prefix))

        if not branches:  # No company found
            return default

        # Try to get the HQ
        for branch in branches:
            if branch[0].startswith(hq_prefix):
                return branch[1]

        # HQ not found, try to get a company with this CNPJ
        for branch in branches:
            if branch[0] == cnpj:
                return branch[1]

        # Nope, let's return the first branch found
        return branches[0][1]

    def serialize_pj(self, partnership):
        return {
            'cnpj_root': partnership['cpf_cnpj_socio'].upper()[:8],
            'nome': self.get_company_name(partnership['cpf_cnpj_socio'], default=partnership['nome_socio']),
            'codigo_qualificacao_socio': partnership['codigo_qualificacao_socio'],
            'qualificacao_socio': partnership['qualificacao_socio'],
            'cnpj_root_emp': partnership['cnpj'].upper()[:8],
            'nome_emp': self.get_company_name(partnership['cnpj'], default=partnership['razao_social']),
        }

    def serialize_pf(self, partnership):
        return {
            'cpf': (partnership['cpf_cnpj_socio'] or '').upper(),
            'nome': partnership['nome_socio'].upper(),
            'cnpj_root': partnership['cnpj'].upper()[:8],
            'nome_emp': self.get_company_name(partnership['cnpj'], default=partnership['razao_social']),
            'codigo_qualificacao_socio': partnership['codigo_qualificacao_socio'],
            'qualificacao_socio': partnership['qualificacao_socio'],
        }

    def serialize_ext(self, partnership):
        return {
            'cpf_cnpj': (partnership['cpf_cnpj_socio'] or '').upper(),
            'nome': partnership['nome_socio'].upper(),
            'codigo_qualificacao_socio': partnership['codigo_qualificacao_socio'],
            'qualificacao_socio': partnership['qualificacao_socio'],
            'cnpj_root_emp': partnership['cnpj'].upper()[:8],
            'nome_emp': self.get_company_name(partnership['cnpj'], default=partnership['razao_social']),
        }

    def execute(self):
        self.load_companies()

        serializers = {
            '1': self.serialize_pj,
            '2': self.serialize_pf,
            '3': self.serialize_ext,
        }
        writers = {
            '1': CsvLazyDictWriter('../data/graph-pjs.csv.gz'),
            '2': CsvLazyDictWriter('../data/graph-pfs.csv.gz'),
            '3': CsvLazyDictWriter('../data/graph-ext.csv.gz'),
        }
        fobj = io.TextIOWrapper(
            lzma.open('../data/socios-brasil/socios.csv.xz'),
            encoding='utf-8',
        )
        for partnership in tqdm(csv.DictReader(fobj)):
            partner_type = partnership['codigo_tipo_socio']
            row = serializers[partner_type](partnership)
            writers[partner_type].writerow(row)


if __name__ == '__main__':
    ExportGraph().execute()
