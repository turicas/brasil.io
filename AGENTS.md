# AGENTS.md

> Brasil.IO torna dados públicos brasileiros mais acessíveis por meio de datasets, API e interface Web em Django.

## Atalhos Usando Alvos `make`

- Preparar serviços: `make build start`; acompanhar: `make logs`; encerrar: `make stop`
- Abrir _shell_ no serviço `web`: `make bash`; como _root_: `make bash-root`
- Testes com cobertura: `make test`; teste selecionado: `TEST_ARGS="-k nome_do_teste" make test`
- Formatar e checar: `make lint`; só verificar: `make lint-check`
- Django: `make migrations`, `make migrate`, `make shell` e `make dbshell`
- Limpar cache Django: `make clear-cache`
- CI local: `make lint-check-ci` e `make test-ci`

No host, os alvos de aplicação usam `docker compose exec` no serviço `web`. Dentro da imagem de desenvolvimento, esses alvos rodam diretamente no container. A mesma regra vale quando `ENV_TYPE` estiver definido com outro valor que não `production`. A imagem de desenvolvimento possui `git`, `make`, `rg` e `tree`. Alvos que administram Docker Compose (`build`, `start`, `stop`, `logs`, `clean`, `bash-root`) continuam destinados ao host, não use-os dentro do container.

A configuração local fica em `docker/env/<servico>.local`, é ignorada pelo Git e carregada após `docker/env/<servico>` (que é versionada). Os serviços devem rodar minimamente sem precisar de novas definições de variáveis de ambiente. Depois de alterá-las, use `make restart`.

## Arquitetura

- `project/settings.py` contém as configurações específicas do Brasil.IO e importa `project/base_settings.py`, que é a base de configuração do [cookiecutter-dokku-django](https://github.com/PythonicCafe/cookiecutter-dokku-django). Não mova configurações do projeto para o arquivo base sem necessidade comprovada.
- As apps do projeto são `api`, `brasilio_auth`, `core`, `covid19`, `dashboard` e `traffic_control`. Preserve suas fronteiras ao implementar uma mudança.
- O serviço `web` inicia migrações e a aplicação HTTP. `worker` e `mail-worker` reutilizam a imagem e executam processamento assíncrono; `messaging` é Redis, `db` é PostgreSQL, `storage` é MinIO e `mail` (local) é MailHog.
- Dados de datasets são importados por comandos Django. Não versionar arquivos baixados, bancos, dados em `docker/data/`, credenciais ou arquivos `.local`.

## Python e Django

- Siga antes o estilo do módulo alterado. O projeto usa `black`, `isort`, `autoflake` e `flake8` pelo `lint.sh`; não introduza `ruff` sem uma migração deliberada.
- Em código novo, prefira `pathlib.Path`, _type hints_ modernos e `csv` da _stdlib_ para CSV. Não introduza `pandas`.
- Todo I/O externo precisa de _timeout_. Não usar `except: pass`; trate exceções específicas e `KeyboardInterrupt` separadamente.
- Nomes do domínio, mensagens, campos e documentação em PT-BR, sem acentos nos identificadores. Código genérico pode usar Inglês. Preserve o idioma de comentários e _docstrings_ existentes.
- Nunca criar _migrations_ de _schema_ manualmente. Alterações de modelos devem incluir a _migration_ gerada por `make migrations` e ser validadas com `make migrate`.
- Chamadas externas lentas não devem ocorrer em _views_. Use o mecanismo assíncrono já adotado pelo projeto quando a operação precisar ocorrer fora da requisição.
- Alterações em API devem preservar autenticação, permissões, paginação e versionamento definidos em `project/settings.py` e em `project/api_urls.py`.

## Frontend

- O padrão atual em `develop` é Django Templates com Materialize e jQuery. Preserve-o enquanto trabalhar neste branch e não inicie uma segunda migração de interface.
- O padrão planejado está em `origin/enhancement/upgrade-bootstrap-2`, que ainda precisa de _rebase_: Django Templates, Bootstrap 5, Bootstrap Icons e SCSS. Ao trabalhar nesse branch, siga o padrão dele, não o de `develop`.
- Nesse padrão novo, altere SCSS-fonte em `static_src/scss/`, organizado entre `components/` e `layouts/`, e regenere `static/css/main.css` pelo processo definido em `static_src/package.json`. Não edite o CSS gerado.
- Reutilize componentes, grade responsiva e APIs JavaScript do Bootstrap antes de criar CSS ou JavaScript próprios. Mantenha jQuery somente nas integrações existentes, como DataTables.
- Componentes novos devem funcionar nos temas claro, escuro e automático. Use classes e variáveis do Bootstrap, não cores fixas. Preserve HTML semântico, navegação por teclado, textos em PT-BR e nomes acessíveis; ícones não substituem texto.
- Reutilize _partials_ e componentes existentes para mensagens, formulários e navegação. Valide os estados normal, vazio, carregando e erro, além das larguras de tela relevantes.

## CLI e Comandos

- Para CLIs fora do Django, use `argparse`, `main()` e `if __name__ == "__main__":`. Para ações integradas à aplicação, use _management commands_ do Django.
- Argumentos obrigatórios são posicionais; opções com `--` são modificadores opcionais. Valide formatos com tipos e _parsers_ explícitos; caminhos usam `pathlib.Path`.
- Dados produzidos pelo comando vão para _stdout_; progresso, avisos e erros vão para _stderr_. Não imprima mensagens de sucesso sem conteúdo útil.
- Use código `0` para sucesso e código diferente de zero para falha. O `--help` deve permitir usar o comando sem ler o código.
- Nunca passe senhas, _tokens_ ou outros segredos pela linha de comando - prefira variáveis de ambiente e/ou arquivos de configuração. Operações demoradas devem informar andamento em _stderr_, permitir interrupção limpa e processar dados incrementalmente/retomada automática quando necessário.

## Testes e Dados

- Use `pytest` com `assert` direto e `model_bakery` para criar objetos Django. Escreva testes de comportamento e regressão próximos à app correspondente; não substitua integração disponível por _mocks_ genéricos.
- Execute `make test` e `make lint-check` antes de concluir. Para alterações de _schema_, execute também as migrations.
- Trate fontes de dados como contratos voláteis: inspecione formato, _encoding_, colunas e valores no conjunto inteiro antes de normalizar. Não descarte campos ou valores sem registrar a decisão.
- CPFs e CNPJs devem ser armazenados como texto (e a partir de julho/2026, CNPJ pode ter letras também). Preserve o valor recebido e remova somente formatação `.-/` quando necessário; nunca trate CPF ou CNPJ como número.

## Linguagem e Comunicação

- Escreva de forma direta, concreta e em Português claro. Explique decisões pelo problema, evidência, consequência e solução.
- Evite jargão genérico quando houver formulação comum: "imagem de desenvolvimento", "roda no container" e "regra" são preferíveis a abstrações desnecessárias.
- Não invente fatos nem esconda incertezas. Diga o que foi confirmado, o que é hipótese e o que não pôde ser executado.
- A comunicação pública do Brasil.IO é próxima e assertiva, mas baseada em fontes, exemplos e limitações verificáveis, sempre referenciados por links. Não simule informalidade nem transforme documentação técnica em texto burocrático.
- O [Blog do Brasil.IO](https://blog.brasil.io/) está no repositório <https://github.com/PythonicCafe/blog.brasil.io/> e você deve sugerir publicar algo quando mudanças relevantes forem implementadas.

## Git e Documentação

- Preserve mudanças preexistentes. Não use `git add .`, `git reset`, `git checkout` destrutivo ou limpezas indiscriminadas.
- Commits são atômicos, em PT-BR e no presente do indicativo: `Adiciona`, `Corrige`, `Remove`. Revise os arquivos incluídos antes de cada commit.
- Atualize `README.md`, `AGENTS.md` ou a documentação em `docs/` quando mudar comandos, ambiente de desenvolvimento, comportamento público ou importação de dados. Consulte `docs/dev-setup.md` antes de alterar o fluxo de desenvolvimento.

Se encontrar uma suposição incorreta neste arquivo, proponha sua correção antes de concluir a tarefa.
