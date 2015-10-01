# coding: utf-8

from os import unlink
from os.path import join as path_join
from tempfile import NamedTemporaryFile

from fabric.api import env, put, prefix, run, settings, task
from fabric.contrib.files import exists


APP_PATH = '/home/turicas/api.brasil.io'
VENV_PATH = path_join(APP_PATH, 'venv')
API_URL = 'https://api.brasil.io/'
UWSGI_CONFIG = {
        'APP_PATH': APP_PATH,
        'PID_PATH': path_join(APP_PATH, 'uwsgi.pid'),
        'LOG_PATH': path_join(APP_PATH, 'uwsgi.log'),
        'PROCESSES': '4',
        'SOCKET': '127.0.0.1:8001',
        'VENV_PATH': VENV_PATH,
        'STATS': '127.0.0.1:8002',
}

env.hosts = ['api.brasil.io']
env.user = 'turicas'
env.activate = 'source {}/bin/activate'.format(VENV_PATH)

@task
def create_and_update_virtualenv():
    if not exists(APP_PATH):
        run('mkdir {}'.format(APP_PATH))
    if not exists(VENV_PATH):
        run('virtualenv {}'.format(VENV_PATH))

    put('requirements/production.txt', path_join(APP_PATH, 'requirements.txt'))
    with prefix(env.activate):
        run('pip install -r {}'.format(path_join(APP_PATH,
            'requirements.txt')))

@task
def send_files():
    if not exists(APP_PATH):
        run('mkdir {}'.format(APP_PATH))

    put('api.py', APP_PATH)
    put('dados_brasil.py', APP_PATH)
    put('geojsons.json', APP_PATH)
    put('topojsons.json', APP_PATH)

    temporary_file = NamedTemporaryFile(delete=False)
    with open('config.py') as fobj:
        contents = fobj.read()
    contents = contents.replace('http://127.0.0.1:8000/', API_URL)
    temporary_file.file.write(contents)
    temporary_file.close()
    put(temporary_file.name, path_join(APP_PATH, 'config.py'))
    unlink(temporary_file.name)

@task
def restart_uwsgi():
    path = path_join(APP_PATH, 'uwsgi.ini')
    temporary_file = NamedTemporaryFile(delete=False)
    with open('uwsgi.ini') as fobj:
        contents = fobj.read()
    for key, value in UWSGI_CONFIG.items():
        contents = contents.replace('{{{{{}}}}}'.format(key), value)
    temporary_file.file.write(contents)
    temporary_file.close()

    put(temporary_file.name, path)
    unlink(temporary_file.name)

    pid_path = UWSGI_CONFIG['PID_PATH']
    run('touch {}'.format(pid_path))
    with prefix(env.activate):
        with settings(warn_only=True):
            run('uwsgi --stop {}'.format(UWSGI_CONFIG['PID_PATH']))
        run('uwsgi --ini {}'.format(path))

@task
def deploy():
    create_and_update_virtualenv()
    send_files()
    restart_uwsgi()
