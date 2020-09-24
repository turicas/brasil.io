#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

python manage.py rqscheduler
