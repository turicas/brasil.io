# coding: utf-8

import unittest

from json import loads as json_loads

from attrdict import AttrDict

import api


class TestBrasilIOAPI(unittest.TestCase):
    def setUp(self):
        api.app.config['TESTING'] = True
        self.app = api.app.test_client()

    def json_get(self, url, status_code=False):
        response = self.app.get(url, follow_redirects=True)
        data = AttrDict(json_loads(response.data))
        if status_code:
            data.status_code = response.status_code
        return data

    @unittest.skip('TODO: implementar')
    def test_meta(self):
        response = self.json_get('/')
        self.assertIn('meta', response)
        meta = response.data['meta']

    @unittest.skip('TODO: implementar')
    def test_regioes(self):
        response = self.json_get('/')
        self.assertIn('regioes', response)
        regioes = response.regioes

    def test_listagem_de_unidades_federativas(self):
        response = self.json_get('/')
        self.assertIn('unidades_federativas', response)
        unidades_federativas = response.unidades_federativas
        self.assertEqual(len(unidades_federativas), 27)

        chaves_necessarias = {'codigo-ibge', 'url', 'sigla', 'nome'}
        for uf in unidades_federativas:
            self.assertEquals(set(uf.keys()), chaves_necessarias)

        nomes = [uf['nome'] for uf in unidades_federativas]
        self.assertEqual(sorted(nomes), nomes)

        self.assertEqual(self.json_get('/rj/'), self.json_get('/rj'))

    def test_listagem_de_municipios_possui_chaves_necessarias(self):
        chaves_necessarias = {'codigo-ibge', 'url', 'sigla', 'nome',
                'municipios'}
        unidades_federativas = self.json_get('/').unidades_federativas
        for uf in unidades_federativas:
            municipios_uf = self.json_get(uf['url'])
            self.assertEqual(set(municipios_uf.keys()), chaves_necessarias)

    def test_unidade_federativa_nao_existe(self):
        erro_esperado = u'Unidade Federativa não encontrada.'
        nao_existe = self.json_get('/na', status_code=True)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, erro_esperado)
        nao_existe = self.json_get('/ab/non-ecziste', status_code=True)
        self.assertEqual(nao_existe.erro, erro_esperado)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, erro_esperado)

    def test_municipios_possuem_chaves_necessarias(self):
        rj = self.json_get('/rj')
        self.assertEqual(len(rj.municipios), 92)

        chaves_necessarias = {'codigo-ibge', 'url', 'nome'}
        for municipio in rj.municipios:
            self.assertEqual(set(municipio.keys()), chaves_necessarias)

    def test_municipios_aparecem_em_ordem_alfabetica(self):
        unidades_federativas = self.json_get('/').unidades_federativas
        for uf in unidades_federativas:
            municipios = self.json_get(uf['url']).municipios
            nomes = [municipio['nome'] for municipio in municipios]
            self.assertEqual(nomes, sorted(nomes))

    def xtest_municipio(self):
        nao_existe = self.json_get('/rj/non-ecziste', status_code=True)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, u'Município não encontrado.')

        tres_rios = self.json_get('/rj/tres-rios')
        chaves_necessarias = {'codigo-ibge', 'url', 'nome'} # TODO: ?
        self.assertEqual(set(tres_rios.keys()), chaves_necessarias)
