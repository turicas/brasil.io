# coding: utf-8

# Generate 'geo/' and 'topo/' by running 'make'. Download:
# https://github.com/carolinabigonha/br-atlas

import json


lines = [x.split() for x in open('sha1geo.txt').read().decode('utf-8').splitlines()]
geojsons = {}
for sha1sum, filename in lines:
    uf = filename.split('/')[1].split('-')[0]
    if uf not in geojsons:
        geojsons[uf] = []
    geojsons[uf].append({'url': 'http://data.brasil.io/{}/{}'.format(uf, filename.split('-')[1].replace('.json', '.geo.json')), 'sha1sum': sha1sum, })
with open('geojsons.json', 'w') as fobj:
    json.dump(geojsons, fobj)

lines = [x.split() for x in open('sha1topo.txt').read().decode('utf-8').splitlines()]
topojsons = {}
for sha1sum, filename in lines:
    uf = filename.split('/')[1].split('-')[0]
    if uf not in topojsons:
        topojsons[uf] = []
    topojsons[uf].append({'url': 'http://data.brasil.io/{}/{}'.format(uf, filename.split('-')[1].replace('.json', '.topo.json')), 'sha1sum': sha1sum, })
with open('topojsons.json', 'w') as fobj:
    json.dump(topojsons, fobj)
