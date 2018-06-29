import csv
import gzip
import io
from collections import defaultdict

from django.core.management.base import BaseCommand
from py2neo import Relationship
from tqdm import tqdm

from core.models import Dataset
from graphs.connection import get_graph_db_connection


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


class Command(BaseCommand):
    help = 'Import socios-brasil data to Neo4J DB'

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)

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
            "cnpj_root": partnership.cpf_cnpj_socio.upper()[:8],
            "nome": self.get_company_name(partnership.cpf_cnpj_socio, default=partnership.nome_socio),
            'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
            'qualificacao_socio': partnership.qualificacao_socio,
            "cnpj_root_emp": partnership.cnpj.upper()[:8],
            "nome_emp": self.get_company_name(partnership.cnpj, default=partnership.razao_social),
        }

    def serialize_pf(self, partnership):
        return {
            "cpf": (partnership.cpf_cnpj_socio or '').upper(),
            "nome": partnership.nome_socio.upper(),
            "cnpj_root": partnership.cnpj.upper()[:8],
            "nome_emp": self.get_company_name(partnership.cnpj, default=partnership.razao_social),
            'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
            'qualificacao_socio': partnership.qualificacao_socio,
        }

    def serialize_ext(self, partnership):
        return {
            "cpf_cnpj": (partnership.cpf_cnpj_socio or '').upper(),
            "nome": partnership.nome_socio.upper(),
            'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
            'qualificacao_socio': partnership.qualificacao_socio,
            "cnpj_root_emp": partnership.cnpj.upper()[:8],
            "nome_emp": self.get_company_name(partnership.cnpj, default=partnership.razao_social),
        }

    def load_tables(self):
        self.Documentos = Dataset.objects.get(slug='documentos-brasil')\
                                         .get_table('documents').get_model()
        self.SociosBrasil = Dataset.objects.get(slug='socios-brasil')\
                                           .get_table('socios').get_model()

    def load_companies(self):
        companies = defaultdict(list)
        qs = self.Documentos.objects.filter(document_type='CNPJ')
        for company in tqdm(qs.iterator(), total=qs.count()):
            companies[int(company.document[:8])].append(
                # Storing as a tuple to save memory
                (company.document, company.name)
            )
        self.companies = companies

    def handle(self, *args, **kwargs):
        self.load_tables()

        # Before start, let's cache companies based on docroot
        print('Loading companies in memory to speed up the process')
        self.load_companies()

        # First step: serialize data to CSV, split by partnership type
        print('Exporting data to CSV')
        serializers = {
            1: self.serialize_pj,
            2: self.serialize_pf,
            3: self.serialize_ext,
        }
        writers = {
            1: CsvLazyDictWriter('pjs.csv.gz'),
            2: CsvLazyDictWriter('pfs.csv.gz'),
            3: CsvLazyDictWriter('ext.csv.gz'),
        }
        qs = self.SociosBrasil.objects.all()
        total = self.SociosBrasil.objects.count()
        for partnership in tqdm(qs.iterator(), total=total):
            partner_type = partnership.codigo_tipo_socio
            row = serializers[partner_type](partnership)
            writers[partner_type].writerow(row)

        # Second step: create needed indexes
        # TODO: connect to the database and execute queries
        #CREATE CONSTRAINT ON (PessoaJuridica) ASSERT PessoaJuridica.cnpj_root IS UNIQUE;
        #CREATE CONSTRAINT ON (PessoaFisica) ASSERT PessoaFisica.nome IS UNIQUE;
        #CREATE CONSTRAINT ON (NomeExterior) ASSERT NomeExterior.nome IS UNIQUE;

        # Third step: bulk import CSV data into Neo4J
        # TODO: execute bulk queries
        #pfs_query = """
        #    UNWIND {batches} AS r
        #    MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root })
        #    ON CREATE SET c.nome=r.nome_emp
        #    ON MATCH SET c.nome=r.nome_emp
        #    MERGE (p:PessoaFisica { nome: r.nome })
        #    ON CREATE SET p.cpf=r.cpf
        #    ON MATCH SET p.cpf=r.cpf
        #    CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        #"""
        #pjs_query = """
        #    UNWIND {batches} as r
        #    MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root_emp })
        #    ON CREATE SET c.nome=r.nome_emp
        #    ON MATCH SET c.nome=r.nome_emp
        #    MERGE (p:PessoaJuridica { cnpj_root: r.cnpj_root })
        #    ON CREATE SET p.nome=r.nome
        #    CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        #"""
        #ext_query = """
        #    UNWIND {batches} as r
        #    MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root_emp })
        #    ON CREATE SET c.nome=r.nome_emp
        #    ON MATCH SET c.nome=r.nome_emp
        #    MERGE (p:NomeExterior { nome: r.nome })
        #    ON CREATE SET p.cpf_cnpj=r.cpf_cnpj
        #    ON MATCH SET p.cpf_cnpj=r.cpf_cnpj
        #    CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        #"""
