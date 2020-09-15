# Processo de desenvolvimento

### Comandos para desenvolvimento

O Brasil.io tem por prática o hábito de manter testes unitários para garantir o funcionamento esperado do sistema. Portanto, uma boa forma de saber se suas alterações não quebrarm a aplicação, execute os testes com:

```
make test
```

Além disso, o nosso [processo de Integração Contínua](https://github.com/turicas/brasil.io/blob/develop/.github/workflows/django.yml) também espera que o código respeite algumas regras como, por exemplo, não deixarmos importações de código não utilizados.

Para garantir que seu código está no formato ideal, execute:

```
make lint
```

Por fim, uma maneira mais segura de rodar toda aplicação (Django + cache zerado) em um único comando é:

```
make run
```

Nosso arquivo [Makefile](https://github.com/turicas/brasil.io/blob/develop/Makefile) possui outras entradas que podem te ser úteis durante o processo de desenvolvimento.

### Padrões de arquivos de apps

O projeto segue alguns padrões de organização dos arquivos das apps Django. Mais especificamente em relação aos arquivos estáticos, templates e de testes.

- **Testes:** os arquivos de testes de uma app devem estar sempre dentro do diretório `tests`, como por examplo, `meu_app/tests`. Cada arquivo de teste deve refletir qual módulo da app está sendo testado seguindo o padrão de nome `test_{modulo}.py`. Portanto, se você quiser criar novos testes para o `models.py` em sua nova app, eles devem estar em `meu_app/tests/test_models.py`;
- **Templates:** o diretório [`templates`](https://github.com/turicas/brasil.io/tree/develop/templates) da aplicação deve ter somente templates base ou globais do sistema. Caso você precise criar alguma nova página na sua app, organize o template da seguinte forma: `meu_app/templates/meu_app/{template_name}.html`. Essa estratégia é para garantir namespaces para que apps diferentes possam utilizar templates como mesmo nome (exemplo `core/templates/core/index.html` e `meu_app/templates/meu_app/index.html`);
- **Arquivos estáticos:** os arquivos estáticos obedecem ao mesmo princípio de namespaces dos templates, assim como o diretório base [`static`](https://github.com/turicas/brasil.io/tree/develop/static) tem como princípio organizar arquivos de estilo, javascript e imagens base do projeto. Assim, organize seus arquivos estáticos em `meu_app/static/meu_app/img/minha_image.png` ou `meu_app/static/meu_app/css/meu_estilo.css` ou `meu_app/static/meu_app/js/meu_javascript.js`;
