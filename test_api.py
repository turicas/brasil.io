# coding: utf-8

import unittest

from json import loads as json_loads

from attrdict import AttrDict

import api


class TestBrasilIOAPI(unittest.TestCase):
    def setUp(self):
        api.app.config['TESTING'] = True
        self.app = api.app.test_client()

    def json_get(self, url, status_code=False, follow_redirects=True):
        response = self.app.get(url, follow_redirects=follow_redirects)
        content_type = response.headers['Content-Type'].split(';')[0].strip()
        if content_type == 'application/json':
            data = AttrDict(json_loads(response.data))
        else:
            data = AttrDict({'data': response.data})
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
            self.assertEqual(set(uf.keys()), chaves_necessarias)
            self.assertEqual(uf['url'][-1], '/')

        nomes = [uf['nome'] for uf in unidades_federativas]
        self.assertEqual(sorted(nomes), nomes)

        self.assertEqual(self.json_get('/rj/'), self.json_get('/rj'))
        self.assertEqual(self.json_get('/rj/'), self.json_get('/RJ/'))

    def test_unidade_federativa_nao_existe(self):
        erro_esperado = u'Unidade Federativa não encontrada.'
        nao_existe = self.json_get('/na', status_code=True)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, erro_esperado)
        nao_existe = self.json_get('/ab/non-ecziste', status_code=True)
        self.assertEqual(nao_existe.erro, erro_esperado)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, erro_esperado)

    def test_listagem_de_municipios_possui_chaves_necessarias(self):
        chaves_necessarias = {'codigo-ibge', 'url', 'sigla', 'nome',
                'municipios'}
        unidades_federativas = self.json_get('/').unidades_federativas
        for uf in unidades_federativas:
            municipios_uf = self.json_get(uf['url'])
            self.assertEqual(set(municipios_uf.keys()), chaves_necessarias)

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
            nomes = []
            for municipio in municipios:
                nomes.append(municipio['nome'])
                self.assertEqual(municipio['url'][-1], '/')
            self.assertEqual(nomes, sorted(nomes))

    def test_municipio_nao_existe(self):
        nao_existe = self.json_get('/rj/non-ecziste', status_code=True)
        self.assertEqual(nao_existe.status_code, 404)
        self.assertEqual(nao_existe.erro, u'Município não encontrado.')

    def test_municipio_deve_retornar_chaves_necessarias(self):
        tres_rios = self.json_get('/rj/tres-rios', status_code=True,
                follow_redirects=False)
        self.assertEqual(tres_rios.status_code, 301)
        self.assertEqual(self.json_get('/rj/tres-rios'),
                         self.json_get('/rj/tres-rios/'))

        tres_rios = self.json_get('/rj/tres-rios/')
        chaves_necessarias = {'codigo-ibge', 'url', 'nome'} # TODO: ?
        self.assertEqual(set(tres_rios.keys()), chaves_necessarias)

    def test_deve_aceitar_requisicoes_jsonp(self):
        content_type = 'Content-Type'
        json_type = 'application/json'
        jsonp_type = 'application/javascript'
        urls = ['/', '/rj/', '/rj/tres-rios/']

        for url in urls:
            normal = self.app.get(url)
            jsonp = self.app.get(url + '?callback=myCallback')
            self.assertEqual('myCallback({});'.format(normal.data), jsonp.data)
            self.assertEqual(normal.headers[content_type], json_type)
            self.assertEqual(jsonp.headers[content_type], jsonp_type)

    def test_deve_aceitar_requisicoes_cors_simples(self):
        content_type = 'Content-Type'
        expected_type = 'application/json'
        urls = ['/', '/rj/', '/rj/tres-rios/']

        for url in urls:
            normal = self.app.get(url)
            self.assertNotIn('Access-Control-Allow-Origin', normal.headers)
            self.assertEqual(normal.headers[content_type], expected_type)

            cors = self.app.get(url, headers={'Origin': 'http://example.com'})
            self.assertIn('Access-Control-Allow-Origin', cors.headers)
            self.assertEqual(cors.headers['Access-Control-Allow-Origin'], '*')
            self.assertEqual(cors.headers[content_type], expected_type)
