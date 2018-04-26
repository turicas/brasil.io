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

    def create_indexes(self):
        objects = [PessoaJuridica, PessoaFisica, NomeExterior]
        for graph_obj in objects:
            graph_db.schema.create_uniqueness_constraint(
                graph_obj.__primarylabel__, graph_obj.__primarykey__
            )

    def get_company(self, partnership):
        company = PessoaJuridica.select(graph_db, partnership.cnpj_empresa).first()

        if not company:
            company = PessoaJuridica()
            company.nome = partnership.nome_empresa.upper()
            company.cnpj = partnership.cnpj_empresa.upper()
            company.uf = partnership.unidade_federativa.upper()
        elif not company.uf and partnership.unidade_federativa:
            company.uf = partnership.unidade_federativa.upper()

        return company

    def get_company_partner(self, partnership):
        company = PessoaJuridica.select(graph_db, partnership.cpf_cnpj_socio).first()

        if not company:
            company = PessoaJuridica()
            company.nome = partnership.nome_socio.upper()
            company.cnpj = partnership.cpf_cnpj_socio.upper()

        return company

    def get_person_partner(self, partnership):
        person = PessoaFisica.select(graph_db, partnership.nome_socio).first()

        if not person:
            person = PessoaFisica()
            person.nome = partnership.nome_socio.upper()
            person.cpf = (partnership.cpf_cnpj_socio or '').upper()

        return person

    def get_foreigner_partner(self, partnership):
        partner = NomeExterior.select(graph_db, partnership.nome_socio).first()

        if not partner:
            partner = NomeExterior()
            partner.nome = partnership.nome_socio.upper()
            partner.cpf_cnpj = (partnership.cpf_cnpj_socio or '').upper()

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

    def get_partnership_properties(self, partnership):
        return {
            'codigo_qualificacao_socio': partnership.codigo_qualificacao_socio,
            'qualificacao_socio': partnership.qualificacao_socio,
        }

    def handle(self, *args, **kwargs):
        SociosBrasil = self.get_socios_brasil_model()

        start = time.time()

        print('Criando índices no banco Neo4J')
        self.create_indexes()
        print('Importando os sócios para o Neo4J')
        for partnership in SociosBrasil.objects.iterator():
            node_start = time.time()
            company = self.get_company(partnership)
            partner = self.get_partner(partnership)
            partnership_data = self.get_partnership_properties(partnership)

            partner.empresas.add(company, properties=partnership_data)
            graph_db.push(partner)
            node_end = time.time()
            print('  {:.6f}s.'.format(node_end - node_start))

        end = time.time()
        print('  finalizado em {:.3f}s.'.format(end - start))
