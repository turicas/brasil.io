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
make build start logs
```

O processo acima deve demorar alguns  minutos para executar, pois irá construir a imagem Docker que executará o Django
e baixará as demais imagens/dependências. Quando finalizar e tudo estiver rodando, execute `make bash` para acessar o
shell do container com o Django e então execute dentro do container:

```shell
# Importa metadados dos datasets atuais:
python manage.py update_data
# Cria super usuário:
python manage.py createsuperuser --username=admin --email=admin@brasil.io
```

Pronto! A plataforma poderá ser acessada pelo seu navegador Web em [localhost:5000](http://localhost:5000/).

> Nota: para diferenciar o domínio da API, utilizamos o domínio `api.localhost` nas configurações, então ela deve ser
> acessada por [api.localhost:5000](http://api.localhost:5000/) e você deve criar uma entrada de `api.localhost` em seu
> `/etc/hosts` que deve resolver `127.0.0.1`.

Caso termine de trabalhar no projeto e queira parar os serviços, execute:

```shell
make stop
```

Nas próximas vezes que for trabalhar no projeto, basta executar um comando:

```shell
make start logs
```

> Nota: o banco de dados principal (PostgreSQL) foi configurado para ser executado
   em um computador com 8 cores, 16GB de RAM e SSD. Caso esse não seja seu computador, considere alterar o arquivo
   `docker/conf/db/postgresql.dev.conf` (você precisará reiniciar o serviço `db` do docker compose). Para saber as
   melhores configurações para sua máquina, consulte o [PgTune](https://pgtune.leopard.in.ua/).


## Serviços

Os serviços definidos no Docker compose são os seguintes:

- `web`: executa o Django, acessível em [localhost:5000](http://localhost:5000/)
- `db`: executa o PostgreSQL, sem encaminhamento de porta da máquina host (você pode conectar ao shell do
  banco executando `make dbshell` ou `docker compose exec web python manage.py dbshell`)
- `messaging`: executa o Redis (para cache e fila de tarefas), sem encaminhamento de porta da máquina host (você pode
  conectar-se a ele executando `docker compose exec messaging redis-cli`)
- `worker`: executa o mesmo container do Django, porém rodando o worker do RQ (em vez do `gunicorn`)
- `storage`: executa o MinIO (equivalente ao AWS S3), acessível em [localhost:9000](http://localhost:9000/) (API) e
  [localhost:9001](http://localhost:9001/) (console).
- `mail`: executa o Mailhog (para verificar os emails enviados), acessível em [localhost:8025](http://localhost:8025/)

## Importando Dados

Antes de importar dados em um dataset, você precisa executar o script de importação de dados ou baixar os dados já
convertidos. Nesse exemplo, vamos baixar algumas tabelas de diversos datasets e executar o comando de importação para
cada uma delas. Antes, abra o shell do container `web` executando `make bash`. Depois, execute dentro do container os
comandos abaixo:

```shell
# Os comandos devem ser executados DENTRO do container `web`:
mkdir -p /data/covid19 /data/genero-nomes

cd /data/covid19
wget https://data.brasil.io/dataset/covid19/caso_full.csv.gz
wget https://data.brasil.io/dataset/covid19/caso.csv.gz
wget https://data.brasil.io/dataset/covid19/boletim.csv.gz
wget https://data.brasil.io/dataset/covid19/obito_cartorio.csv.gz
cd /app
python manage.py import_data --no-input --unlogged covid19 caso_full /data/covid19/caso_full.csv.gz
python manage.py import_data --no-input --unlogged covid19 caso /data/covid19/caso.csv.gz
python manage.py import_data --no-input --unlogged covid19 boletim /data/covid19/boletim.csv.gz
python manage.py import_data --no-input --unlogged covid19 obito_cartorio /data/covid19/obito_cartorio.csv.gz

cd /data/genero-nomes
wget https://data.brasil.io/dataset/genero-nomes/nomes.csv.gz
wget https://data.brasil.io/dataset/genero-nomes/grupos.csv.gz
cd /app
python manage.py import_data --no-input --unlogged genero-nomes nomes /data/genero-nomes/nomes.csv.gz
python manage.py import_data --no-input --unlogged genero-nomes grupos /data/genero-nomes/grupos.csv.gz
```

Para cada arquivo CSV (que pode estar comprimido), o comando `import_data` executará os seguintes passos:

- Criar uma nova tabela, usando os metadados sobre ela que estão em `Table` e `Field` e seguindo o padrão
  `data_<dataset>_<tabela>_<aleatorio>`;
- Criar um gatilho no PostgreSQL para preenchimento automático do índice de busca de texto completo para os campos que
  precisam dessa busca (estão descritos nos metadados);
- Importar os dados do CSV usando
  [`rows.utils.pgimport`](https://github.com/turicas/rows/blob/develop/rows/utils.py#L580) (que usa o comando COPY da
  interface de linha de comando `psql`);
- Rodar o comando SQL `VACUUM ANALYSE` para que o PostgreSQL preencha estatísticas sobre a tabela (isso ajudará a
  melhorar o desempenho de diversas consultas);
- Criar os índices em campos que estão marcados como possíveis de serem usados como filtros na interface, para otimizar
  a busca;
- Preencher um cache em `Field` contendo todas as possíveis opções para os campos que estão marcados como "choiceable"
  (são os campos filtráveis e que possuem poucas opções de valor, como unidade federativa, ano etc.).

> **Nota 1**: você pode pular algumas das etapas acima passando as opções `--no-xxx` para o comando.
>
> **Nota 2**: a opção `--unlogged` do comando `import_data` executará a importação mais rapidamente, mas fará com que a
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


## Comandos para desenvolvimento

O Brasil.IO tem por prática o hábito de manter testes unitários para garantir o funcionamento esperado do sistema.
Portanto, uma boa forma de saber se suas alterações não quebrarm a aplicação, execute os testes com:

```
make test  # use test-v para a versão detalhada do pytest (verbose)
```

Além disso, o nosso [processo de integração
contínua](https://github.com/turicas/brasil.io/blob/develop/.github/workflows/django.yml) também espera que o código
respeite algumas regras como, por exemplo, não deixarmos importações de código não utilizados. Para garantir que seu
código está no formato ideal, execute:

```
make lint
```

Veja mais comandos úteis executando `make help`.


## Personalizando variáveis de ambiente

Para cada serviço, temos um arquivo de variáveis de ambiente padrão chamado `docker/env/<serviço>`. Essa arquivo é
versionado no Git e deve ter apenas opções que se aplicam a todas as pessoas que desenvolvem o projeto. Caso precise alterar
alguma das variáveis, utilize um arquivo `docker/env/<serviço>.local`, que não é versionado e possui precedência na
definição das variáveis sobre as do arquivo versionado.
