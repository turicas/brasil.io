# coding: utf-8
from flask_restful import Resource, reqparse
from underscore import _
import json

class Estados(Resource):
    def get(self, sigla=None):

        if sigla:
            sigla = sigla.lower()
            
            return _.find(data, lambda o, *a: o['sigla'] == sigla)
        else:
            return data

data = json.load(open('./data/estados.json'))