import time
from py2neo import Relationship
from tqdm import tqdm

from django.core.management.base import BaseCommand

from core.models import Table
from graphs.connection import graph_db
from graphs.nodes import PessoaJuridica, PessoaFisica, NomeExterior


class Command(BaseCommand):
    help = 'Import socios-brasil data to Neo4J DB'

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)
        self.open_transaction = None
        self.batch_size = 1000

    def create_indexes(self):
        objects = [PessoaJuridica, PessoaFisica, NomeExterior]
        for graph_obj in objects:
            graph_db.schema.create_uniqueness_constraint(
                graph_obj.__primarylabel__, graph_obj.__primarykey__
            )

    def get_socios_brasil_model(self):
        table = Table.objects.get(dataset__slug='socios-brasil')
        return table.get_model()

    def get_pfs_query_and_params(self, pfs):
        query = """
            UNWIND {batches} AS r
            MERGE (c:PessoaJuridica { cnpj: r.cnpj })
            ON CREATE SET c.uf=r.uf, c.nome=r.nome_emp
            ON MATCH SET c.uf=r.uf, c.nome=r.nome_emp
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
                "cnpj": partnership.cnpj_empresa.upper(),
                "uf": partnership.unidade_federativa.upper(),
                "nome_emp": partnership.nome_empresa.upper(),
                'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
                'qualificacao_socio': partnership.qualificacao_socio,
            })

        return query, {'batches': batches}

    def get_pjs_query_and_params(self, pjs):
        query = """
            UNWIND {batches} as r
            MERGE (c:PessoaJuridica { cnpj: r.cnpj_emp })
            ON CREATE SET c.uf=r.uf, c.nome=r.nome_emp
            ON MATCH SET c.uf=r.uf, c.nome=r.nome_emp
            MERGE (p:PessoaJuridica { cnpj: r.cnpj })
            ON CREATE SET p.nome=r.nome
            ON MATCH SET p.nome=r.nome
            CREATE (p)-[:TEM_SOCIEDADE { codigo_tipo_socio: r.codigo_qualificacao_socio, qualificacao_socio: r.qualificacao_socio }]->(c)
        """

        batches = []
        for partnership in pjs:
            batches.append({
                "cnpj": (partnership.cpf_cnpj_socio or '').upper(),
                "nome": partnership.nome_socio.upper(),
                'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
                'qualificacao_socio': partnership.qualificacao_socio,
                "cnpj_emp": partnership.cnpj_empresa.upper(),
                "nome_emp": partnership.nome_empresa.upper(),
                "uf": partnership.unidade_federativa.upper(),
            })

        return query, {'batches': batches}

    def get_ext_query_and_params(self, ext):
        query = """
            UNWIND {batches} as r
            MERGE (c:PessoaJuridica { cnpj: r.cnpj_emp })
            ON CREATE SET c.uf=r.uf, c.nome=r.nome_emp
            ON MATCH SET c.uf=r.uf, c.nome=r.nome_emp
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
                "cnpj_emp": partnership.cnpj_empresa.upper(),
                "nome_emp": partnership.nome_empresa.upper(),
                "uf": partnership.unidade_federativa.upper(),
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
        with tqdm(desc='Importando lotes de 1000 registros', total=num_batches) as progress:
            pfs, pjs, ext = [], [], []
            for i, partnership in enumerate(SociosBrasil.objects.iterator()):
                if not i % self.batch_size:
                    open_transaction = graph_db.begin()

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
            open_transaction.commit()

        end = time.time()
        duration = int((end - start) / 60)
        print('  + Finalizado em {} min ({} lotes, {} lote/min)'.format(
            duration, num_batches, num_batches / duration
        ))
        print("Importação realizada com sucesso terminada")
