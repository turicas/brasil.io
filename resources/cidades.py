# coding: utf-8
from flask_restful import Resource, reqparse
from underscore import _
import json


parser = reqparse.RequestParser()
parser.add_argument(
    'fontes', 
    type=str,
    location='args',
    action='append'
)


class Cidades(Resource):
    def get(self, sigla, slug=None):
        sigla = sigla.lower()

        if slug:
            args = parser.parse_args()
            
            cidade = _.find(cidades[sigla], 
                lambda o, *a: o['slug'] == slug
            )

            return cidade
        else:
            return cidades[sigla]


cidades = json.load(open('./data/cidades.json'))
ibge_codigos = json.load(open('./data/ibge/cidades-codigo.json'))