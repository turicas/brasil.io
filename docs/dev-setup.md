# Setup para Desenvolvimento

O projeto e todos os serviços necessários (como bancos de dados) rodam completamente dentro de *containers* Docker.
Para rodá-lo localmente, você precisa ter instalado em seu computador:

- [git](https://git-scm.com/)
- [Docker](https://docker.io/)

Existem outras formas de rodar o projeto localmente, como executando o Django na própria máquina (fora de um
*container*), porém recomendamos utilizar *containers* para simplificar o processo e evitar conflitos de versões.


## Criação do Ambiente Local

Para começar, faça um clone local do repositório original:

```shell
git clone https://github.com/turicas/brasil.io
```

Entre no repositório, construa e inicie os *containers*:

```shell
cd brasil.io
make build start
```

O processo acima deve demorar em torno de 10 minutos para executar, pois irá construir a imagem Docker que executará o
Django e baixará as demais imagens/dependências. Quando finalizar e tudo estiver rodando, execute `make bash` para
acessar o shell do container com o Django e então execute dentro do container:

```shell
# Importa metadados dos datasets atuais
python manage.py update_data
# Cria super usuário:
python manage.py createsuperuser --username=admin --email=admin@brasil.io
```

Pronto! A plataforma poderá ser acessada pelo seu navegador Web em
[localhost:4200](http://localhost:4200).

Caso termine de trabalhar no projeto e queira parar os serviços, execute:

```shell
make stop
```

Nas próximas vezes que for trabalhar no projeto, basta executar um comando:

```shell
make start
```

> Sugestão: use `make start logs` para acompanhar os logs durante o desenvolvimento.

> Nota: o banco de dados principal (PostgreSQL) foi configurado para ser executado
   em um computador com 8 cores, 16GB de RAM e SSD. Caso esse não seja seu computador, considere alterar o arquivo
   `docker/conf/db/postgresql.dev.conf` (você precisará reiniciar o serviço `db` do docker compose). Para saber as
   melhores configurações para sua máquina, consulte o [PgTune](https://pgtune.leopard.in.ua/).


## Importando Dados

Antes de importar dados em um dataset, você precisa executar o script de importação de dados ou baixar os dados já
convertidos. Nesse exemplo, vamos baixar algumas tabelas de diversos datasets e executar o comando de importação para
cada uma delas. Antes, abra o shell do container `web` executando `make bash`. Depois, execute dentro do container os
comandos abaixo:

```shell
mkdir -p data/covid19 data/genero-nomes

cd data/covid19
wget https://data.brasil.io/dataset/covid19/caso_full.csv.gz
wget https://data.brasil.io/dataset/covid19/caso.csv.gz
wget https://data.brasil.io/dataset/covid19/boletim.csv.gz
wget https://data.brasil.io/dataset/covid19/obito_cartorio.csv.gz
cd -
python manage.py import_data --no-input --unlogged covid19 caso_full data/covid19/caso_full.csv.gz
python manage.py import_data --no-input --unlogged covid19 caso data/covid19/caso.csv.gz
python manage.py import_data --no-input --unlogged covid19 boletim data/covid19/boletim.csv.gz
python manage.py import_data --no-input --unlogged covid19 obito_cartorio data/covid19/obito_cartorio.csv.gz

cd data/genero-nomes
wget https://data.brasil.io/dataset/genero-nomes/nomes.csv.gz
wget https://data.brasil.io/dataset/genero-nomes/grupos.csv.gz
cd -
python manage.py import_data --no-input --unlogged genero-nomes nomes data/genero-nomes/nomes.csv.gz
python manage.py import_data --no-input --unlogged genero-nomes grupos data/genero-nomes/grupos.csv.gz
```

> Nota: a opção `--unlogged` do comando `import_data` executará a importação mais rapidamente, mas fará com que a
> tabela possa ser perdida caso os dados do PostgreSQL sejam corrompidos (e também não será replicada, caso existam
> réplicas configuradas). Em geral, para ambientes de desenvolvimento, essas questões não são problemas.


## Contribuindo

1. Crie um *fork* do projeto em sua conta no GitHub, clicando no botão "*fork*"
   em <https://github.com/turicas/brasil.io>
2. Caso já tenha clonado o repositório original localmente, adicione seu *fork*
   como um repositório remoto com o comando:
   `git remote add <seu-username> https://github.com/<seu-username>/brasil.io`.
3. Caso ainda não tenha clonado o repositório em sua máquina, clone-o com o
   comando: `git clone https://github.com/<seu-username>/brasil.io`.
4. Crie um *branch* em seu repositório local para trabalhar nas alterações que
   deseja, onde você executará os *commits*.
5. Suba seu *branch* para seu *fork* com o comando
   `git push <seu-username> <nome-do-branch>` e crie um *pull request* no
   repositório principal.
