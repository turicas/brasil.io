import time
from django.core.management.base import BaseCommand

from core.models import Table

from graphs.nodes import PessoaJuridica, PessoaFisica, NomeExterior
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
            company.uf = partnership.unidade_federativa.upper()
            graph_db.push(company)
        elif not company.uf and partnership.unidade_federativa:
            company.uf = partnership.unidade_federativa.upper()
            graph_db.push(company)

        return company

    def get_company_partner(self, partnership):
        company = PessoaJuridica.select(graph_db, partnership.cpf_cnpj_socio).first()

        if not company:
            company = PessoaJuridica()
            company.nome = partnership.nome_socio.upper()
            company.cnpj = partnership.cpf_cnpj_socio.upper()
            graph_db.push(company)

        return company

    def get_person_partner(self, partnership):
        person = PessoaFisica.select(graph_db, partnership.nome_socio).first()

        if not person:
            person = PessoaFisica()
            person.nome = partnership.nome_socio.upper()
            person.cpf = (partnership.cpf_cnpj_socio or '').upper()
            graph_db.push(person)

        return person

    def get_foreigner_partner(self, partnership):
        partner = NomeExterior.select(graph_db, partnership.nome_socio).first()

        if not partner:
            partner = NomeExterior()
            partner.nome = partnership.nome_socio.upper()
            partner.cpf_cnpj = (partnership.cpf_cnpj_socio or '').upper()
            graph_db.push(partner)

        return partner

    def get_partner(self, partnership):
        partner_type = partnership.codigo_tipo_socio
        if partner_type == 1:
            return self.get_company_partner(partnership)
        elif partner_type == 2:
            return self.get_person_partner(partnership)
        elif partner_type == 3:
            return self.get_foreigner_partner(partnership)
        else:
            msg = 'Sódio {} - {} é um tipo inválido.'.format(
                partnership.codigo_tipo_socio, partnership.tipo_socio
            )
            raise ValueError(msg)

    def handle(self, *args, **kwargs):
        SociosBrasil = self.get_socios_brasil_model()

        print('Importando os sócios para o Neo4J')
        start = time.time()
        for partnership in SociosBrasil.objects.all()[:100].iterator():
            company = self.get_company(partnership)
            partner = self.get_partner(partnership)

        end = time.time()
        print('  finalizado em {:.3f}s.'.format(end - start))
