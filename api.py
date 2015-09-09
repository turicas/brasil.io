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
    '/estados',
    '/estados/<string:sigla>')
api.add_resource(Cidades, 
    '/estados/<string:sigla>/cidades',
    '/estados/<string:sigla>/cidades/<string:slug>')

if __name__ == '__main__':
    app.run(debug=True)