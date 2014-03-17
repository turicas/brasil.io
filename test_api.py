# coding: utf-8

import unittest

from json import loads as json_loads

from attrdict import AttrDict

import api


class TestBrasilIOAPI(unittest.TestCase):
    def setUp(self):
        api.app.config['TESTING'] = True
        self.app = api.app.test_client()

    def json_get(self, url):
        response = self.app.get(url)
        return AttrDict(json_loads(response.data))

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

    def test_unidades_federativas(self):
        response = self.json_get('/')
        self.assertIn('unidades_federativas', response)
        unidades_federativas = response.unidades_federativas
        self.assertEqual(len(unidades_federativas), 27)
        chaves_necessarias = {'codigo-ibge', 'url', 'sigla', 'nome'}
        for uf in unidades_federativas:
            self.assertEquals(set(uf.keys()), chaves_necessarias)

        rj = [uf for uf in unidades_federativas if uf['sigla'] == 'rj'][0]
        rj = self.json_get(rj['url'])
        chaves_necessarias.add('municipios')
        self.assertEqual(set(rj.keys()), chaves_necessarias)

    def test_municipios(self):
        rj = self.json_get('/rj')
        self.assertEqual(len(rj.municipios), 92)

        chaves_necessarias = {'codigo-ibge', 'url', 'nome'}
        for municipio in rj.municipios:
            self.assertEqual(set(municipio.keys()), chaves_necessarias)
