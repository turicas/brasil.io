# Setup para desenvolvimento

Nesta página você encontrará informações sobre como preparar o seu ambiente local para conseguir rodar o projeto, importar dados, executar os testes e poder começar a contribuir no código do Brasil.io.

## Passos gerais

1. Copie o projeto para o seu usuário. Na página do repositório (<https://github.com/turicas/brasil.io>), use o botão "Fork", no canto superior direito

2. Certifique-se de que você tenha instalados:

- git
- [pyenv](https://github.com/pyenv/pyenv) com
  [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) e Python 3.7.9

3. Clone seu repositório na máquina em que for trabalhar:

```bash
# Clonar o repositório:
git clone https://github.com/<seu-usuario-github>/brasil.io.git
```

4. Há duas formas de rodar o projeto em sua máquina, uma utilizando o PostgreSQL como um container Docker e outra utilizando o PostgreSQL rodando diretamente em sua máquina. Aqui você vai encontrar o processo para ambas as formas.

### Configuração usando Docker

1. Certifique-se de que você tenha instalado o [docker](https://www.docker.com/).

Esse exemplo usa o script em get.docker.com para instalar a última versão do Docker Engine - Community no Linux.

Aviso: Sempre examine scripts baixados da internet antes de rodá-los localmente.

```bash

# Para instalar o docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Para permitir seu usuário rodar comandos docker sem "sudo"
sudo usermod -aG docker $USER
sudo service docker restart

```

Além disso é necessário ter também o
[`docker-compose`](https://docs.docker.com/compose/install/) configurado:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
docker-compose --version
```

Lembre-se de sair do terminal e entrar novamente, para que produza o efeito desejado!

2. Entre na pasta brasil.io e siga os passos:

```bash

cd brasil.io

# Instale o Python 3.7.9 usando o pyenv:
pyenv install 3.7.9

# Criar um virtualenv:
pyenv virtualenv 3.7.9 brasil.io

# Copie o arquivo de env de exemplo e edite o .env de acordo com suas preferências
cp env.example .env

# Ativar o virtualenv
source .activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar os containers (bancos de dados, e-mail)
docker-compose up -d

# Criar schema e popular base de dados
python manage.py migrate
python manage.py update_data

# Iniciar o servidor HTTP
python manage.py runserver
```

### Configuração sem usar o Docker

1. Certifiques-e de que você tenha instalado o [PostgreSQL](https://www.postgresql.org/)

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
# Instale o Python 3.7.9 usando o pyenv:
pyenv install 3.7.9

# Criar um virtualenv:
pyenv virtualenv 3.7.9 brasil.io

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
