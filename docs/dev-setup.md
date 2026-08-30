# Configuração para desenvolvimento

O projeto e todos os serviços necessários (como bancos de dados) rodam completamente dentro de _containers_ Docker.
Para rodá-lo localmente, você precisará de docker, docker compose e make.

Apesar de existirem outras formas de rodar o projeto localmente (como executando o Django em um virtualenv),
recomendamos utilizar a forma descrita nesse documento, para simplificar o processo e evitar conflitos de versões.

Rodando todos os serviços:

```shell
make build start logs
```

> Nota: a primeira vez que o comando acima for executado irá demorar alguns minutos, pois irá construir a imagem Docker
> que executará o Django e baixará as demais imagens/dependências. As próximas vezes serão bem mais rápidas (e basta
> executar `make start logs`, sem a etapa `build`).

Para acessar o Django, entre em [localhost:5000](http://localhost:5000). O serviço `web` do docker compose irá executar
as migrações antes de iniciar o servidor HTTP, então o sistema já estará pronto para usar (mas ainda sem dados).

Para criar um super usuário no Django (que dá acesso ao Django Admin), execute:

```shell
docker compose exec -it web python manage.py createsuperuser
# ou `make bash` e então, dentro do shell container, `python manage.py createsuperuser`
```

Para executar os testes automatizados, execute (fora do container):

```shell
make test
```

Caso queira rodar apenas algum teste específico, passe opções para o `pytest` por meio da variável `TEST_ARGS`:
```shell
TEST_ARGS="-k test_run_only_this_one" make test
```

Para forçar o guia de estilos em todo o código Python, execute (fora do container):

```shell
make lint
```

Para ver mais atalhos que ajudam no processo de desenvolvimento, execute `make help`.


## Personalizando variáveis de ambiente

Cada serviço definido no Docker compose possui um arquivo de variável de ambiente chamado `docker/env/<serviço>`. Se
você precisa trocar qualquer um dos valores padrão, crie um arquivo chamado `docker/env/<serviço>.local` e coloque-as
lá. Esse arquivo será ignorado pelo Git e o Docker compose irá carregá-lo após o primeiro, sobrescrevendo os valores.
Dessa forma, evitamos colocar credenciais e outros dados sensíveis no repositório.

**Atenção**: não se esqueça de executar `make restart` para que a mudança nas variáveis de ambiente faça efeito (não
adianta reiniciar apenas o container do serviço que teve variáveis alteradas, é preciso reiniciar o docker compose
completamente).

> Nota: caso você precise adicionar alguma variável de ambiente que será usada por todos da equipe obrigatoriamente,
> defina pelo menos um valor fictício no arquivo principal, para que todos consigam executar corretamente.


## Serviços

Os serviços configurados no Docker compose são:

- `web`: container principal da aplicação Web, rodando o Django e acessível por
  [localhost:5000](http://localhost:5000/);
- `worker`: utiliza a mesma imagem do container `web`, mas executa o worker do rq (em vez do servidor HTTP), para
  processar as tarefas em segundo plano;
- `db`: executa o banco de dados, sem encaminhamento de porta da máquina host (você pode conectar ao shell do banco
  executando `make dbshell` ou `docker compose exec web python manage.py dbshell`);
- `mail`: executa o Mailhog (para verificar os emails enviados), acessível em [localhost:8025](http://localhost:8025/);
- `messaging`: executa o Redis (cache no banco 0, fila de tarefas no banco 1; em produção são duas instâncias, ver
  `docs/deploy.md`), sem encaminhamento de porta da máquina host (você pode conectar-se a ele executando
  `docker compose exec messaging redis-cli`);
- `storage`: executa o MinIO (equivalente ao AWS S3), acessível em [localhost:9000](http://localhost:9000/) (API) e
  [localhost:9001](http://localhost:9001/) (console).


## Acesso à API local

Para diferenciar o domínio da API, utilizamos o domínio `api.localhost` nas configurações, então ela deve ser acessada
por [api.localhost:5000](http://api.localhost:5000/) e você deve criar uma entrada de `api.localhost` em seu
`/etc/hosts` que deve resolver `127.0.0.1`.


## Importando Dados

Antes de importar os dados dos datasets, execute o comando que importa metadados dos datasets atuais dentro do shell do
container web (execute `make bash`):

```shell
python manage.py update_data
```

O comando acima irá baixar os metadados, que estão disponíveis na Web, e salvará em seu banco de dados local.

Para importar os dados em um dataset, você precisa executar o script de importação de dados ou baixar os dados já
convertidos. Nesse exemplo, vamos baixar algumas tabelas de diversos datasets e executar o comando de importação para
cada uma delas. Antes, abra o shell do container `web` executando `make bash`. Depois, execute dentro do container os
comandos abaixo:

```shell
# Os comandos devem ser executados DENTRO do container `web`:
cd /app

mkdir -p /data/covid19
for table in caso_full caso boletim obito_cartorio; do
  url="https://data.brasil.io/dataset/covid19/${table}.csv.gz"
  filename="/data/covid19/${table}.csv.gz"
  wget -O "$filename" "$url"
  python manage.py import_data --no-input --unlogged covid19 $table "$filename"
done

mkdir -p /data/genero-nomes
for table in nomes grupos; do
  url="https://data.brasil.io/dataset/genero-nomes/${table}.csv.gz"
  filename="/data/genero-nomes/${table}.csv.gz"
  wget -O "$filename" "$url"
  python manage.py import_data --no-input --unlogged genero-nomes $table "$filename"
done
```

Para cada arquivo CSV (que pode estar comprimido), o comando `import_data` executará os seguintes passos:

- Criar uma nova tabela, usando os metadados sobre ela que estão em `Table` e `Field` e seguindo o padrão
  `data_<dataset>_<tabela>_<string-aleatoria>`;
- Criar um gatilho no PostgreSQL para preenchimento automático do índice de busca de texto completo para os campos que
  precisam dessa busca (estão descritos nos metadados);
- Importar os dados do CSV usando
  [`rows.plugins.postgresql.pgimport`](https://github.com/turicas/rows/blob/develop/rows/plugins/plugin_postgresql.py#L600)
  (que usa o comando COPY da interface de linha de comando `psql`);
- Rodar o comando SQL `VACUUM ANALYSE` para que o PostgreSQL preencha estatísticas sobre a tabela (isso ajudará a
  melhorar o desempenho de diversas consultas);
- Criar os índices em campos que estão marcados como possíveis de serem usados como filtros na interface, para otimizar
  as consultas;
- Preencher um cache em `Field` contendo todas as possíveis opções para os campos que estão marcados como "choiceable"
  (são os campos filtráveis e que possuem variáveis categóricas, como unidade federativa, ano etc.).

> **Nota 1**: você pode pular algumas das etapas acima passando as opções `--no-xxx` para o comando.
>
> **Nota 2**: a opção `--unlogged` do comando `import_data` executará a importação mais rapidamente, mas fará com que a
> tabela possa ser perdida caso os dados do PostgreSQL sejam corrompidos (e também não será replicada, caso existam
> réplicas configuradas). Em geral, para ambientes de desenvolvimento, essas questões não são problemas.


## Criando um _Pull Request_

1. Crie um _fork_ do projeto em sua conta no GitHub, clicando no botão "_fork_"
   em <https://github.com/turicas/brasil.io>
2. Caso já tenha clonado o repositório original localmente, adicione seu _fork_
   como um repositório remoto com o comando:
   `git remote add <seu-username> https://github.com/<seu-username>/brasil.io`.
3. Caso ainda não tenha clonado o repositório em sua máquina, clone-o com o
   comando: `git clone https://github.com/<seu-username>/brasil.io`.
4. Crie um _branch_ em seu repositório local para trabalhar nas alterações que
   deseja, onde você executará os _commits_.
5. Suba seu _branch_ para seu _fork_ com o comando
   `git push <seu-username> <nome-do-branch>` e crie um _pull request_ no
   repositório principal.


## Boas práticas

O Brasil.IO tem por prática o hábito de manter testes unitários para garantir o funcionamento esperado do sistema.
Portanto, ao colaborar com novas funcionalidades, implemente testes automatizados e execute `make test` para garantir
que suas alterações não quebraram o restante do que estava implementado.

Além disso, o [processo de integração
contínua](https://github.com/turicas/brasil.io/blob/develop/.github/workflows/django.yml) também espera que o código
respeite algumas regras como, por exemplo, não deixarmos importações de código não utilizados. Para garantir que seu
código está no formato esperado, sempre execute `make lint` antes de fazer seus commits.
