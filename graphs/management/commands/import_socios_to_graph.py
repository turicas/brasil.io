import time
from py2neo import Relationship
from tqdm import tqdm

from django.core.management.base import BaseCommand

from core.models import Table
from graphs.connection import get_graph_db_connection


class Command(BaseCommand):
    help = 'Import socios-brasil data to Neo4J DB'

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)
        self.open_transaction = None
        self.batch_size = 1000
        self.graph_db = get_graph_db_connection()
        self.company_names = {}

    @property
    def Documentos(self):
        if not getattr(self, '_Documentos', None):
            self._Documentos = Table.objects.for_dataset('documentos-brasil').named('documents').get_model()
        return self._Documentos

    def create_indexes(self):
        labels_keys = [
            ('PessoaJuridica', 'cnpj_root'),
            ('PessoaFisica', 'nome'),
            ('NomeExterior', 'nome'),
        ]
        for label, key in labels_keys:
            self.graph_db.schema.create_uniqueness_constraint(label, key)

    def get_socios_brasil_model(self):
        table = Table.objects.for_dataset('socios-brasil').named('socios')
        return table.get_model()

    def get_emp_name(self, cnpj, default):
        cnpj_prefix = cnpj[:8]

        if cnpj_prefix not in self.company_names:
            headquarter_prefix = cnpj_prefix + '0001'
            branches = self.Documentos.objects.filter(
                docroot=cnpj_prefix,
                document_type='CNPJ',
            )

            if branches.exists():
                try:
                    company = branches.get(document__startswith=headquarter_prefix)
                except self.Documentos.DoesNotExist:
                    try:
                        company = branches.get(document=cnpj)
                    except self.Documentos.DoesNotExist:
                        company = branches[0]
                self.company_names[cnpj_prefix] = company.name
            else:
                self.company_names[cnpj_prefix] = default

        return self.company_names[cnpj_prefix]

    def get_pfs_query_and_params(self, pfs):
        query = """
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
                "cpf": (partnership.cpf_cnpj_socio or '').upper(),
                "nome": partnership.nome_socio.upper(),
                "cnpj_root": partnership.cnpj.upper()[:8],
                "nome_emp": self.get_emp_name(partnership.cnpj, default=partnership.razao_social),
                'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
                'qualificacao_socio': partnership.qualificacao_socio,
            })

        return query, {'batches': batches}

    def get_pjs_query_and_params(self, pjs):
        query = """
            UNWIND {batches} as r
            MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root_emp })
            ON CREATE SET c.nome=r.nome_emp
            ON MATCH SET c.nome=r.nome_emp
            MERGE (p:PessoaJuridica { cnpj_root: r.cnpj_root })
            ON CREATE SET p.nome=r.nome
            CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        """

        batches = []
        for partnership in pjs:
            batches.append({
                "cnpj_root": partnership.cpf_cnpj_socio.upper()[:8],
                "nome": self.get_emp_name(partnership.cpf_cnpj_socio, default=partnership.nome_socio),
                'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
                'qualificacao_socio': partnership.qualificacao_socio,
                "cnpj_root_emp": partnership.cnpj.upper()[:8],
                "nome_emp": self.get_emp_name(partnership.cnpj, default=partnership.razao_social),
            })

        return query, {'batches': batches}

    def get_ext_query_and_params(self, ext):
        query = """
            UNWIND {batches} as r
            MERGE (c:PessoaJuridica { cnpj_root: r.cnpj_root_emp })
            ON CREATE SET c.nome=r.nome_emp
            ON MATCH SET c.nome=r.nome_emp
            MERGE (p:NomeExterior { nome: r.nome })
            ON CREATE SET p.cpf_cnpj=r.cpf_cnpj
            ON MATCH SET p.cpf_cnpj=r.cpf_cnpj
            CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        """

        batches = []
        for partnership in ext:
            batches.append({
                "cpf_cnpj": (partnership.cpf_cnpj_socio or '').upper(),
                "nome": partnership.nome_socio.upper(),
                'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
                'qualificacao_socio': partnership.qualificacao_socio,
                "cnpj_root_emp": partnership.cnpj.upper()[:8],
                "nome_emp": self.get_emp_name(partnership.cnpj, default=partnership.razao_social),
            })

        return query, {'batches': batches}

    def handle(self, *args, **kwargs):
        print('Importando os sócios para o Neo4J...\n')
        start = time.time()

        SociosBrasil = self.get_socios_brasil_model()
        total = SociosBrasil.objects.count()
        num_batches = int(total / self.batch_size)

        open_transaction = None
        self.create_indexes()
        with tqdm(total=num_batches) as progress:
            pfs, pjs, ext = [], [], []
            for i, partnership in enumerate(SociosBrasil.objects.iterator()):
                if not i % self.batch_size:
                    open_transaction = self.graph_db.begin()

                partner_type = partnership.codigo_tipo_socio
                if partner_type == 1:  # Pessoa Jurídica
                    pjs.append(partnership)
                elif partner_type == 2:  # Pessoa Física
                    pfs.append(partnership)
                elif partner_type == 3:  # Nome Exterior
                    ext.append(partnership)

                if not (i + 1) % self.batch_size:
                    query, params = self.get_pfs_query_and_params(pfs)
                    if params:
                        open_transaction.run(query, parameters=params)

                    query, params = self.get_pjs_query_and_params(pjs)
                    if params:
                        open_transaction.run(query, parameters=params)

                    query, params = self.get_ext_query_and_params(ext)
                    if params:
                        open_transaction.run(query, parameters=params)

                    open_transaction.commit()
                    progress.update(1)
                    open_transaction = None
                    pfs, pjs, ext = [], [], []

        if open_transaction:
            query, params = self.get_pfs_query_and_params(pfs)
            if params:
                open_transaction.run(query, parameters=params)

            query, params = self.get_pjs_query_and_params(pjs)
            if params:
                open_transaction.run(query, parameters=params)

            query, params = self.get_ext_query_and_params(ext)
            if params:
                open_transaction.run(query, parameters=params)

            open_transaction.commit()

        end = time.time()
        duration = int((end - start) / 60)
        print('  + Finalizado em {} min ({} lotes, {} lote/min)'.format(
            duration, num_batches, num_batches / duration
        ))
        print("Importação realizada com sucesso terminada")
