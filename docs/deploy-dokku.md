# Deploy no Dokku

[Dokku](https://github.com/dokku/dokku) é um software *plataform-as-a-service*
software livre, que funciona como um "Heroku do-it-yourself" e facilita
bastante o *deployment* e manutenção de aplicações Web. O *deployment* do
*backend* do [Brasil.IO](https://brasil.io/) é feito utilizando ele (que
depende do [Docker][https://docker.io/]).

Para fazer o *deployment* da plataforma em um servidor Debian GNU/Linux, siga
os seguintes passos:


## Instalação do Docker

```shell
apt remove docker docker-engine docker.io containerd runc
apt update
apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - apt-key fingerprint 0EBFCD88
apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Para testar a instalação, execute:
docker run --rm hello-world
```

## Instalação do Dokku e Plugins

```shell
wget -nv -O - https://packagecloud.io/dokku/dokku/gpgkey | apt-key add -
export SOURCE="https://packagecloud.io/dokku/dokku/ubuntu/"
export OS_ID="$(lsb_release -cs 2>/dev/null || echo "bionic")"
echo "xenial bionic focal" | grep -q "$OS_ID" || OS_ID="bionic"
echo "deb $SOURCE $OS_ID main" | tee /etc/apt/sources.list.d/dokku.list
apt update
apt install -y dokku
dokku plugin:install-dependencies --core

dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres
dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
dokku plugin:install https://github.com/dokku/dokku-maintenance.git maintenance
```

> **Importante:** após a instalação do Dokku, acesse a interface Web temporária
> para finalizar configuração (entre em `http://ip-do-servidor/` em seu
> navegador).


## Criação da Aplicação


```shell
# Mude apenas essas primeiras variáveis
export ADMIN_EMAIL="admin@example.com"
export APP_NAME="brasilio-web"
export COOKIE_DOMAIN=".brasil.io"
export DB_SERVICE_NAME="brasilio_pg13"
export DOMAINS="www.brasil.io,brasil.io,api.brasil.io"
export SENDGRID_API_KEY="<...>"
export FERNET_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

dokku apps:create $APP_NAME
dokku postgres:create $DB_SERVICE_NAME
dokku postgres:link $DB_SERVICE_NAME $APP_NAME

for domain in $(echo $DOMAINS | tr ',' '\n'); do
	dokku domains:add $APP_NAME $domain
done

dokku config:set --no-restart $APP_NAME ADMINS="$ADMIN_NAME|$ADMIN_EMAIL"
dokku config:set --no-restart $APP_NAME ALLOWED_HOSTS="$DOMAINS"
dokku config:set --no-restart $APP_NAME DATA_URL="https://docs.google.com/spreadsheets/d/1-hw07Q7PBGlz2QjOifkwM3T8406OqsGOAWA-fikgW8c/export?format=xlsx"
dokku config:set --no-restart $APP_NAME DEBUG="false"
dokku config:set --no-restart $APP_NAME DOKKU_LETSENCRYPT_EMAIL="$ADMIN_EMAIL"
dokku config:set --no-restart $APP_NAME EMAIL_BACKEND="sgbackend.SendGridBackend"
dokku config:set --no-restart $APP_NAME FERNET_KEY="$FERNET_KEY"
dokku config:set --no-restart $APP_NAME PRODUCTION="true"
dokku config:set --no-restart $APP_NAME SECRET_KEY="$(openssl rand -hex 16)"
dokku config:set --no-restart $APP_NAME SENDGRID_API_KEY="$SENDGRID_API_KEY"
dokku config:set --no-restart $APP_NAME SESSION_COOKIE_DOMAIN="$COOKIE_DOMAIN"

mkdir -p /var/lib/app-data/$APP_NAME
dokku storage:mount $APP_NAME /var/lib/app-data/$APP_NAME:/data
```

## Primeiro Deployment

Em sua máquina local, você precisa clonar esse repositório e executar um `push`
para o servidor onde está o Dokku:

```shell
export APP_NAME="brasilio-web"
export DOKKU_HOST="<ip-ou-host-do-servidor>"
export REPO_URL="https://github.com/turicas/brasil.io"

git clone $REPO_URL brasil.io
cd brasil.io
git remote add dokku dokku@$DOKKU_HOST:$APP_NAME
git push dokku master
```

## Finalizando a Instalação no Servidor

Depois que o primeiro deploy for feito, volte ao servidor para migrar os dados,
criar o super-usuário (administrador), configurar o SSL e aumentar o número de
processos rodando o Django:

```shell
dokku run $APP_NAME python manage.py migrate
dokku run $APP_NAME python manage.py createsuperuser

dokku ps:scale $APP_NAME web=4
dokku letsencrypt $APP_NAME
```


## Adicionando datasets

```shell
# Importe os metadados do dataset:
dokku run $APP_NAME python manage.py update_data

# Rode o script de coleta do dataset e baixe o arquivo `.csv.xz`
# correspondente.
# Envie o arquivo `.csv.gz` para o servidor e coloque-o em
# `/var/lib/app-data/$APP_NAME`

# Execute o comando de importação dos dados:
dokku run $APP_NAME python manage.py import_data <dataset-slug> <tablename> /data/<filename.csv.xz>
```


## Atualizando lista de contribuidores

A lista de contribuidores que aparece no site é lida de um JSON que fica
hospedado em https://data.brasil.io/meta/contribuidores.json - esse arquivo
deve ser gerado e atualizado de tempos em tempos através dos comandos:

```shell
python manage.py collect_contributors data/contribuidores.json
s3cmd put data/contribuidores.json s3://meta/contribuidores.json
```

O *management command* `collect_contributors` acessará a API pública do GitHub
para criar o JSON e então o s3cmd irá enviá-lo para nosso servidor de arquivos
estáticos.

> **ATENÇÃO**: não atualize o arquivo (`s3cmd put`) caso o primeiro comando
> imprima erros.
