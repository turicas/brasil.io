import time

from django.core.management.base import BaseCommand

from graphs.connection import get_graph_db_connection


class Command(BaseCommand):
    help = "Populates EmpresaMae nodes"

    def __init__(self, *args, **kwargs):
        super(BaseCommand, self).__init__(*args, **kwargs)
        self.graph_db = get_graph_db_connection()

    def handle(self, *args, **kwargs):
        start = time.time()
        print('Atualizando nós que são empresas-mães com a query:')
        query = '''
            MATCH (e:PessoaJuridica)-[:TEM_SOCIEDADE]->(:PessoaJuridica)
            WITH DISTINCT e as empresa, COLLECT(e) as companies
            WHERE ALL(c in companies WHERE NOT (:PessoaJuridica)-[:TEM_SOCIEDADE]->(c))
            SET empresa :EmpresaMae
            RETURN COUNT(empresa)
        '''
        print(query)

        output = self.graph_db.data(query)
        num_empresas = output[0]['COUNT(empresa)']

        end = time.time()
        print("Importação realizada com sucesso.")
        print('  + {} empresas consideradas empresas-mãe.'.format(num_empresas))
        print('  + Finalizado em {:7.3f}s'.format(end - start))
