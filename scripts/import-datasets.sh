#!/bin/bash

# This script will run `manage.py import_data` for a list of known datasets.
# You must download the data first (each CSV should be located at:
# `data/<dataset-slug>/<table-name>.csv.xz`).

DATA_PATH="data"
function import_data() {
	DATASET_SLUG=$1
	TABLE_NAME=$2

	time python manage.py import_data --no-input \
		$DATASET_SLUG $TABLE_NAME $DATA_PATH/$DATASET_SLUG/$TABLE_NAME.csv.xz
}

import_data balneabilidade-bahia balneabilidade
import_data balneabilidade-bahia boletins
import_data cursos-prouni cursos
import_data documentos-brasil documents
import_data eleicoes-brasil bens_candidatos
import_data eleicoes-brasil candidatos
import_data eleicoes-brasil filiados
import_data eleicoes-brasil votacoes
import_data gastos-deputados cota_parlamentar
import_data gastos-diretos gastos
import_data salarios-magistrados contracheque
import_data salarios-magistrados genero-nomes grupos
import_data salarios-magistrados genero-nomes nomes
import_data salarios-magistrados links
import_data socios-brasil empresas
import_data socios-brasil holdings
import_data socios-brasil socios

# You may want to create some indexes to speed up some queries:
# TODO: add these indexes to dataset metadata so they'll be created
# automatically.
#CREATE INDEX CONCURRENTLY ON data_documentosbrasil_documents (document_type, name);
#CREATE INDEX CONCURRENTLY ON data_sociosbrasil_socios (qualificacao_socio, razao_social);
#CREATE INDEX CONCURRENTLY ON data_gastosdeputados_cotaparlamentar (txtdescricao, datemissao);
#CREATE INDEX CONCURRENTLY ON data_eleicoesbrasil_votacoes (nome_urna_candidato, numero_cand);
