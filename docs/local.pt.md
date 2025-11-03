# Desenvolvimento local

Esse documento contém algumas dicas para auxiliar no desenvolvimento local.

## Alterando a quantidade de workers

Por padrão, o docker compose irá executar 2 processos de worker. Para alterar esse número temporariamente, você pode
executar o comando abaixo - para alterar para 8, por exemplo:

```shell
docker compose up -d --scale worker=8
```

> Nota: para alterar o valor padrão, altere o valor `deploy.replicas` dentro do serviço `worker` no arquivo
> `compose.yml`.

## Migrando de banco de dados

Se alguém fez uma atualização do postgres nesse repositório e você já tinha dados rodando na versão anterior, ainda não
atualize o código, pois o novo `compose.yml` irá definir o serviço `db` com a nova versão e seus dados estarão na
antiga, o que gerará um conflito.

Não atualize o código para o commit que faz a mudança no compose.yml com a nova versão do banco de dados, mas mude o
código para o commit mais novo possível antes desse, para garantir que os serviços funcionem normalmente. Pare todos os
containers e crie pastas para o banco antigo:

```shell
docker compose down
cp -r docker/conf/db docker/conf/olddb
cp -r docker/env/db docker/env/olddb
mv docker/data/db docker/data/olddb
touch docker/env/db.local docker/env/olddb.local
mkdir docker/data/db
```

Abra o `compose.yml`, copie a definição do serviço `db` e cole-o em outro arquivo temporário. Por exemplo, se a versão
antiga era `postgres:15-bullseye`, adicione o seguinte:

```yaml
  olddb:
    image: "postgres:15-bullseye"
    env_file:
      - path: "docker/env/olddb"
        required: true
      - path: "docker/env/olddb.local"
        required: false
    user: "${UID:-1000}:${GID:-1000}"
    shm_size: "4g"
    command: -c "config_file=/etc/postgresql/postgresql.conf"
    volumes:
      - ${PWD}/docker/data/olddb:/var/lib/postgresql/data
      - ${PWD}/docker/conf/olddb/postgresql.dev.conf:/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 3s
      retries: 5
```

Com o serviço de banco antigo definido, faça a atualização de código:

```shell
git pull
```

Edite o seu arquivo `compose.yml` atualizado e inclua o serviço `db` que você copiou na etapa anterior, mas dê o nome
de `olddb` e nele troque as seguintes referências:
- `docker/conf/db` para `docker/conf/olddb`
- `docker/data/db` para `docker/data/olddb`
- `docker/env/db` para `docker/env/olddb`

Execute apenas os containers dos bancos de dados e verifique se eles estão rodando corretamente pelos logs:

```shell
docker compose up -d olddb db
docker compose logs -ft
```

Verifique nos logs se ambos os serviços mostraram a mensagem "database system is ready to accept connections".

> ATENÇÃO: não use `make start`, senão a aplicação Web irá iniciar e executar as migrações (precisamos que o novo banco
> esteja vazio).

Agora, execute o `bash` no container `web`:

```shell
docker compose run -it --rm web bash
```

E dentro do container, execute:

```shell
export NEW_DB_URL=$DATABASE_URL
export OLD_DB_URL=$(echo $DATABASE_URL | sed 's/@db:/@olddb:/')
echo 'select version()' | psql $OLD_DB_URL
echo 'select version()' | psql $NEW_DB_URL
```

Se os comandos acima não deram erro (e o `psql` conseguiu conectar corretamente em ambos os bancos), execute:

```shell
time pg_dump -F c -d $OLD_DB_URL | pg_restore -d $NEW_DB_URL
```

Após o término, você pode executar `psql $NEW_DB_URL` e verificar se as tabelas existem (`\d`) e se possuem dados
(`SELECT COUNT(*) FROM x`). Depois disso, saia do bash do container `web` e inicie todos os containers:

```shell
make start
```

Para ter certeza de que o banco antigo não irá mais interferir, pare-o com:

```shell
docker compose stop olddb
```

Agora teste a aplicação e verifique se os dados estão aparecendo corretamente. Em caso positivo, apague o serviço
`olddb` do `compose.yml` e delete os arquivos:

```shell
rm -rf docker/conf/olddb docker/data/olddb docker/env/olddb
```

Pronto!
