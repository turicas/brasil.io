#!/bin/bash

import_data() {
	filename="data/$1.csv.xz"
	uncompressed=$(xz -vl "$filename" | grep 'Uncompressed size' | awk '{print $3 "" $4}')
	echo "Importing $1... (uncompressed size: $uncompressed)"
	time python manage.py import_data "$1" "$filename"
}

set -e
import_data balneabilidade-bahia
import_data cursos-prouni
import_data salarios-magistrados
import_data gastos-deputados
import_data socios-brasil
import_data gastos-diretos
