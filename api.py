#!/usr/bin/env python
# coding: utf-8

import argparse
import urllib2

from json import dumps as json_dumps

from flask import Flask, Response

from dados_brasil import unidades_federativas, municipios


url_join = urllib2.urlparse.urljoin
app = Flask(__name__)
BASE_URL = 'http://127.0.0.1:8000/'

# Coloca em memória objetos relativos a UFs
for uf in unidades_federativas:
    uf['url'] = url_join(BASE_URL, uf['sigla'])
ufs = [uf['sigla'] for uf in unidades_federativas]

# Coloca em memória objetos relativos a municípios
for sigla in municipios:
    # TODO: usar flask.url_for
    municipios[sigla]['url'] = url_join(BASE_URL, sigla)
    municipios[sigla]['sigla'] = sigla

    municipios_uf = municipios[sigla]['municipios']
    for municipio in municipios_uf:
        municipio['url'] = url_join(BASE_URL, '{}/{}'
                .format(sigla, municipio['slug']))
        del municipio['slug']

def response_json(data, **kwargs):
    response = {'response': json_dumps(data),
                'status': 200,
                'content_type': 'application/json'}
    response.update(kwargs)
    return Response(**response)

@app.route('/')
def index():
    return response_json({'unidades_federativas': unidades_federativas, })

@app.route('/<sigla>/')
def uf_index(sigla):
    sigla = sigla.lower()
    if sigla not in ufs:
        return Response(status=404) # TODO: retornar algum conteúdo

    return response_json(municipios[sigla])


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
