import time
from django.core.management.base import BaseCommand

from core.models import Table

from graphs.nodes import PessoaJuridica
from graphs.connection import graph_db


class Command(BaseCommand):
    help = 'Import socios-brasil data to Neo4J DB'

    def get_socios_brasil_model(self):
        table = Table.objects.get(dataset__slug='socios-brasil')
        return table.get_model()

    def get_company(self, partnership):
        company = PessoaJuridica.select(graph_db, partnership.cnpj_empresa).first()
        if not company:
            company = PessoaJuridica()
            company.nome = partnership.nome_empresa.upper()
            company.cnpj = partnership.cnpj_empresa.upper()
            graph_db.push(company)
        return company

    def handle(self, *args, **kwargs):
        SociosBrasil = self.get_socios_brasil_model()

        print('Importando os sócios para o Neo4J')
        start = time.time()
        for partnership in SociosBrasil.objects.all()[:100].iterator():
            company = self.get_company(partnership)

        end = time.time()
        print('  finalizado em {:.3f}s.'.format(end - start))
