import csv
import gzip
import io
import os
import time
import glob
from collections import defaultdict

from django.conf import settings
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
        self.graph_db = get_graph_db_connection()

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

    def create_indexes(self):
        labels_keys = [
            ('PessoaJuridica', 'cnpj_root'),
            ('PessoaFisica', 'nome'),
            ('NomeExterior', 'nome'),
        ]
        for label, key in labels_keys:
            self.graph_db.schema.create_uniqueness_constraint(label, key)

    def pfs_query_and_params(self, pfs):
        batch_query = """
            UNWIND {batches} AS r
            MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root })
            ON CREATE SET c.nome=r.nome_emp
            ON MATCH SET c.nome=r.nome_emp
            MERGE (p:PessoaFisica { nome: r.nome })
            ON CREATE SET p.cpf=r.cpf
            ON MATCH SET p.cpf=r.cpf
            CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        """
        batches = []
        for partnership in pfs:
            batches.append({
                "cpf": (partnership['cpf'] or '').upper(),
                "nome": partnership['nome'].upper(),
                "cnpj_root": partnership['cnpj_root'].upper(),
                "nome_emp": partnership['nome_emp'],
                'codigo_qualificacao_socio': partnership['codigo_qualificacao_socio'],
                'qualificacao_socio': partnership['qualificacao_socio'],
            })

        params = {'batches': batches}
        return batch_query, params

    def import_pfs_csv_query(self):
        glob_search = settings.NEO4J_IMPORT_DIR + '/temp-graph-pfs-part-*.csv'
        pfs_csvs = glob.glob(glob_search)

        for abs_path in tqdm(pfs_csvs):
            filename = os.path.basename(abs_path)
            pfs_query = f"""
                USING PERIODIC COMMIT
                LOAD CSV WITH HEADERS FROM "file:///{ filename }" AS r
                MERGE (c:PessoaJuridica {{ cnpj_root: r.cnpj_root }})
                ON CREATE SET c.nome=r.nome_emp
                ON MATCH SET c.nome=r.nome_emp
                MERGE (p:PessoaFisica {{ nome: r.nome }})
                ON CREATE SET p.cpf=r.cpf
                ON MATCH SET p.cpf=r.cpf
                CREATE (p)-[:TEM_SOCIEDADE {{ codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }}]->(c)
            """

            self.graph_db.run(pfs_query)

    def import_pjs_query(self):
        glob_search = settings.NEO4J_IMPORT_DIR + '/temp-graph-pjs-part-*.csv'
        pjs_csvs = glob.glob(glob_search)

        for abs_path in tqdm(pjs_csvs):
            filename = os.path.basename(abs_path)
            pjs_query = f"""
                USING PERIODIC COMMIT
                LOAD CSV WITH HEADERS FROM "file:///{ filename }" AS r
                MERGE (c:PessoaJuridica {{ cnpj_root: r.cnpj_root_emp }})
                ON CREATE SET c.nome=r.nome_emp
                ON MATCH SET c.nome=r.nome_emp
                MERGE (p:PessoaJuridica {{ cnpj_root: r.cnpj_root }})
                ON CREATE SET p.nome=r.nome
                CREATE (p)-[:TEM_SOCIEDADE {{ codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }}]->(c)
            """

            self.graph_db.run(pjs_query)

    def import_ext_query(self):
        ext_query = """
            USING PERIODIC COMMIT
            LOAD CSV WITH HEADERS FROM "file:///graph-ext.csv.gz" AS r
            MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root_emp })
            ON CREATE SET c.nome=r.nome_emp
            ON MATCH SET c.nome=r.nome_emp
            MERGE (p:NomeExterior { nome: r.nome })
            ON CREATE SET p.cpf_cnpj=r.cpf_cnpj
            ON MATCH SET p.cpf_cnpj=r.cpf_cnpj
            CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        """

        self.graph_db.run(ext_query)

    def handle(self, *args, **kwargs):
        main_start = time.time()

        pfs_filename = settings.NEO4J_IMPORT_DIR + '/graph-pfs.csv.gz'
        pjs_filename = settings.NEO4J_IMPORT_DIR + '/graph-pjs.csv.gz'
        ext_filename = settings.NEO4J_IMPORT_DIR + '/graph-ext.csv.gz'

        all_files_exists = all([
            os.path.isfile(pfs_filename),
            os.path.isfile(pjs_filename),
            os.path.isfile(ext_filename),
        ])

        if not all_files_exists:
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
                1: CsvLazyDictWriter(pjs_filename),
                2: CsvLazyDictWriter(pfs_filename),
                3: CsvLazyDictWriter(ext_filename),
            }
            qs = self.SociosBrasil.objects.all()
            total = self.SociosBrasil.objects.count()
            for partnership in tqdm(qs.iterator(), total=total):
                partner_type = partnership.codigo_tipo_socio
                row = serializers[partner_type](partnership)
                writers[partner_type].writerow(row)

        # Second step: create needed indexes

        print('Criando os índices...')
        self.create_indexes()

        start = time.time()
        print('\nCriando sociedades entre pessoas físicas...')
        self.import_pfs_csv_query()
        end = time.time()
        duration = int((end - start) / 60)
        print('  + Finalizado em {} min'.format(duration))

        start = time.time()
        print('Criando sociedades com nomes no exterior...')
        self.import_ext_query()
        end = time.time()
        duration = int((end - start) / 60)
        print('  + Finalizado em {} min'.format(duration))

        start = time.time()
        print('\nCriando sociedades entre pessoas jurídicas...')
        self.import_pjs_query()
        end = time.time()
        duration = int((end - start) / 60)
        print('  + Finalizado em {} min'.format(duration))

        main_end = time.time()
        main_duration = int((main_end - main_start) / 60)
        print('\nToda a importação foi finalizada em {} min'.format(main_duration))
