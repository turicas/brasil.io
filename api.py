#!/usr/bin/env python
# coding: utf-8

import argparse
import urllib2

from json import dumps as json_dumps

from flask import Flask, Response

from dados_brasil import unidades_federativas


url_join = urllib2.urlparse.urljoin
app = Flask(__name__)
BASE_URL = 'http://127.0.0.1:8000/'
for uf in unidades_federativas:
    uf['url'] = url_join(BASE_URL, uf['sigla'])
ufs = [uf['sigla'] for uf in unidades_federativas]


def response_json(data, **kwargs):
    response = {'response': json_dumps(data),
                'status': 200,
                'content_type': 'application/json'}
    response.update(kwargs)
    return Response(**response)

@app.route('/')
def index():
    return response_json({
        'unidades_federativas': unidades_federativas,
        })


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
