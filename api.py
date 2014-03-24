#!/usr/bin/env python
# coding: utf-8

import argparse
import urllib2

from copy import deepcopy
from json import dumps as json_dumps

from flask import Flask, Response, request

from config import BASE_URL
from dados_brasil import unidades_federativas as lista_ufs, municipios


UF_URL = BASE_URL + '{}/'
MUNICIPIO_URL = BASE_URL + '{}/{}/'
url_join = urllib2.urlparse.urljoin
app = Flask(__name__)

# Coloca em memória objetos relativos à listagem de UFs
for uf in lista_ufs:
    uf['url'] = UF_URL.format(uf['sigla'])
ufs = [uf['sigla'] for uf in lista_ufs]

# Coloca em memória objetos relativos a municípios
for sigla in municipios:
    # TODO: usar flask.url_for
    municipios[sigla]['url'] = UF_URL.format(sigla)
    municipios[sigla]['sigla'] = sigla

    municipios_uf = municipios[sigla]['municipios']
    novo = {}
    for municipio in municipios_uf:
        slug = municipio['slug']
        municipio['url'] = MUNICIPIO_URL.format(sigla, slug)
        novo[slug] = municipio
        del municipio['slug']
    municipios[sigla]['municipios'] = novo

# Coloca em memória objetos relativos à listagem de municípios (por UF)
sort_por_nome = lambda a, b: cmp(a['nome'], b['nome'])
municipios_uf = deepcopy(municipios)
for uf in municipios_uf.values():
    uf['municipios'] = sorted(uf['municipios'].values(), cmp=sort_por_nome)


def response_json(data, **kwargs):
    response = {'response': json_dumps(data),
                'status': 200,
                'content_type': 'application/json',
                'headers': {}}
    response.update(kwargs)

    jsonp_callback = request.args.get('callback', None)
    if jsonp_callback is not None:
        response['response'] = u'{}({});'.format(jsonp_callback,
                response['response'])
        response['content_type'] = 'application/javascript'

    return Response(**response)

def http404(mensagem):
    return Response(response=json_dumps({'erro': mensagem}),
                    status=404,
                    content_type='application/json')

@app.route('/')
def index():
    return response_json({'unidades_federativas': lista_ufs, })

@app.route('/<sigla>/')
def uf_index(sigla):
    sigla = sigla.lower()
    if sigla not in ufs:
        return http404(u'Unidade Federativa não encontrada.')
    else:
        return response_json(municipios_uf[sigla])

@app.route('/<sigla>/<municipio>/')
def municipio_index(sigla, municipio):
    sigla, municipio = sigla.lower(), municipio.lower()
    if sigla not in ufs:
        return http404(u'Unidade Federativa não encontrada.')
    elif municipio not in municipios[sigla]['municipios']:
        return http404(u'Município não encontrado.')
    else:
        return response_json(municipios[sigla]['municipios'][municipio])


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--http-host', help='IP address to bind to',
            default='127.0.0.1')
    args.add_argument('--http-port', help='Port to bind to', type=int,
            default=8000)
    args.add_argument('--debug', help='Enable debug mode', action='store_true')
    args.add_argument('--secret-key', default='my-precious')
    args.add_argument('--processes', help='Number of processes to spawn',
            type=int, default=4)
    args.add_argument('--threaded', action='store_true',
            help='Enable/disable HTTP server threaded mode')
    argv = args.parse_args()

    app.config.update({
        'SECRET_KEY': argv.secret_key,
        'DEBUG': argv.debug,
    })

    app.run(host=argv.http_host, port=argv.http_port, processes=argv.processes,
            threaded=argv.threaded)
