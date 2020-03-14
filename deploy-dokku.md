# Deploy no Dokku

[Dokku](https://github.com/dokku/dokku) é um software *plataform-as-a-service*
software livre, que funciona como um "Heroku do-it-yourself" que facilita
bastante o *deployment* e manutenção de aplicações Web. O *deployment* do
*backend* do [Brasil.IO](https://brasil.io/) é feito utilizando ele.

Para montar o ambiente no servidor, você precisa:

- Instalar o Dokku
- Instalar os plugins:
  - `dokku plugin:install https://github.com/dokku/dokku-postgres.git postgres`
  - `dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git`
- Criar a aplicação: `dokku apps:create brasilio-web`
- Criar e linkar o banco de dados PostgreSQL:
  - `dokku postgres:create brasilio_pgsql`
  - `dokku postgres:expose brasilio_pgsql`
  - `dokku postgres:link brasilio_pgsql brasilio-web`
- Configurar as variáveis de ambiente:
  - `dokku config:set brasilio-web DEBUG=False`
  - `dokku config:set brasilio-web SENDGRID_API_KEY=`
  - `dokku config:set brasilio-web ALLOWED_HOSTS=*`
  - `dokku config:set brasilio-web DATA_URL="https://docs.google.com/spreadsheets/d/1-hw07Q7PBGlz2QjOifkwM3T8406OqsGOAWA-fikgW8c/export?format=xlsx"`
  - `dokku config:set brasilio-web PRODUCTION=True`
  - `dokku config:set brasilio-web SECRET_KEY=012345678901234567890123456789`
  - `dokku config:set brasilio-web EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
  - `dokku config:set brasilio-web EMAIL_HOST=localhost`
  - `dokku config:set brasilio-web EMAIL_HOST_USER=`
  - `dokku config:set brasilio-web EMAIL_HOST_PASSWORD=`
  - `dokku config:set brasilio-web EMAIL_PORT=39004`
  - `dokku config:set brasilio-web EMAIL_USE_TLS=False`
  - `dokku config:set brasilio-web ADMINS="programmer|email@example.com"`
  - `dokku config:set brasilio-web FERNET_KEY="1Vo_8aX-WIKEyOWsusu8SHdMDc258elXTN4-WYu_9MQ="`
- Configurar o domínio e o certificado SSL:
  - `dokku domains:add brasilio-web brasil.io`
  - `dokku domains:add brasilio-web api.brasil.io`
  - `dokku domains:add brasilio-web www.brasil.io`
  - `dokku config:set --no-restart brasilio-web DOKKU_LETSENCRYPT_EMAIL=turicas@pythonic.cafe`

Em sua máquina local, você precisa:
- Adicionar o repositório remoto:
  - `git remote add dokku dokku@HOSTNAME:brasilio-web`
- Enviar o código:
  - `git push dokku master`

No servidor, novamente:
- Configurar a quantidade de *workers* do servidor Web:
  - `dokku ps:scale brasilio-web web=4`
- Gerar a chave SSL:
  - `dokku letsencrypt brasilio-web`
- Rodar as migrações iniciais:
  - Rodar um *container*: `dokku run brasilio-web /bin/bash`
  - Dentro do *container*:
    - `cd /app && python manage.py migrate`
    - `cd /app && python manage.py createsuperuser`
    - `cd /app && python manage.py update_data`


## Adicionando datasets

- Rode o script de coleta do dataset e baixe o arquivo `.csv.xz` correspondente
- Envie o arquivo `.csv.gz` para o servidor e coloque-o num diretório, como
  `/root/data`
- Mapeie o diretório para a aplicação Dokku, caso ainda não esteja maepado:
  - `dokku storage:mount brasilio-web /root/data:/data`
- Rode um *container* com a aplicação:
  - `dokku run brasilio-web /bin/bash`
- Dentro do *container*:
  - `cd /app && python manage.py update_data`
  - `cd /app && python manage.py import_data <dataset-slug> <tablename> /data/<filename.csv.xz>`

> Nota: os metadados do dataset precisam estar atualizados na planilha que o
`update_data` baixa.
