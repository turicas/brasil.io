#!/usr/bin/env python
# coding: utf-8

from flask import Flask, make_response
from flask_restful import Api
from resources.estados import Estados
from resources.cidades import Cidades
import json

app = Flask(__name__)
api = Api(app)

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp

api.add_resource(Estados, 
    # Lista todos os estados
    '/estados', 
    # Exibir informações de 1 estado
    '/estados/<string:sigla>')
api.add_resource(Cidades, 
    # Lista todas as cidades de um estado
    '/estados/<string:sigla>/cidades',
    # Exibir informações da cidade de 1 estado
    '/estados/<string:sigla>/cidades/<string:slug>')

if __name__ == '__main__':
    app.run(debug=True)