# Setup para desenvolvimento

Nesta página você encontrará informações sobre como preparar o seu ambiente local para conseguir rodar o projeto, importar dados, executar os testes e poder começar a contribuir no código do Brasil.io.

Há duas formas de rodar o projeto em sua máquina, uma utilizando o PostgreSQL
como um container Docker e outra utilizando o PostgreSQL rodando diretamente
em sua máquina. Aqui você vai encontrar o processo par ambas as formas.

Primeiramente, certifique-se de que você tenha instalados:

- git
- [pyenv](https://github.com/pyenv/pyenv) com
  [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) e Python 3.6.4

### Configuração usando Docker

Certifiques-e de que você tenha instalado o [docker](https://www.docker.com/)
e em seguida clone o repositório:

```bash
# Clonar o repositório:
git clone git@github.com:turicas/brasil.io.git
```

Siga os passos:

```bash
# Instale o Python 3.6.4 usando o pyenv:
pyenv install 3.6.4

# Criar um virtualenv:
pyenv virtualenv 3.6.4 brasil.io

# Copie o arquivo de env de exemplo e edite o .env de acordo com suas preferências
cp env.example .env

# Criar containers e ativar o virtualenv
cd brasil.io
source .activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar os containers (bancos de dados, e-mail)
docker-compose up

# Criar schema e popular base de dados
python manage.py migrate
python manage.py update_data

# Iniciar o servidor HTTP
python manage.py runserver
```

### Configuração sem usar o Docker

Certifiques-e de que você tenha instalado o [PostgreSQL](https://www.postgresql.org/)
e em seguida clone o repositório:

```bash
# Clonar o repositório:
git clone git@github.com:turicas/brasil.io.git

```

Após instalar o PostgreSQL crie o banco de dados que será utilizado pelo
projeto. Como o docker não está sendo utilizado será necessário comentar
algumas linhas no arquivo `.activate`. Comente as seguintes linhas:

```bash
DOCKER_COMPOSE_FILE=docker-compose.yml

if [ -f "$DOCKER_COMPOSE_FILE" ]; then
   docker-compose -p $PROJECT_NAME -f $DOCKER_COMPOSE_FILE up -d
fi
```

e siga os passos:

```bash
# Instale o Python 3.6.4 usando o pyenv:
pyenv install 3.6.4

# Criar um virtualenv:
pyenv virtualenv 3.6.4 brasil.io

# Modifique o arquivo .env para as configurações do seu banco de dados
# Caso você use as configurações padrões, o arquivo será parecido com:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<senha>
POSTGRES_DB=brasilio
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/brasilio

# Ativar o virtualenv
cd brasil.io
source .activate

# Instalar dependências
pip install -r requirements.txt

# Criar schema e popular metadados dos datasets
python manage.py migrate
python manage.py update_data

# Iniciar o servidor HTTP
python manage.py runserver
```
