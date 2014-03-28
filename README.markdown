# `api.brasil.io`

## Introdução

### O Problema

Muitos dados públicos brasileiros estão disponíveis (principalmente depois da
criação da [Lei de Acesso à Informação][lai]), mas não necessariamente
acessíveis. Mesmo que a informação esteja disponível, nem sempre ela está
disponível em um formato legível por máquina, ou utilizando um formato aberto,
ou possui descrição (metadados) que facilitam a interpretação (manual ou
automática) desses dados. Quanto menos acessível é uma informação, mais perto
de ser fechada ela está.

Além do problema relativo à acessibilidade, não existe um lugar comum em que
todos os dados disponíveis estejam organizados e catalogados, dificultando
ainda mais o acesso (ou a descoberta que esse tipo de informação está
disponível).


### A Solução

O projeto [Brasil.IO][brasil.io] foi criado com o objetivo de ser referência
para quem procura ou quer publicar **dados abertos** sobre o Brasil de forma
organizada, [legível por máquina, usando padrões abertos, com dados
referenciáveis e referenciados][5starsopendata].

Foi desenvolvida uma [API HTTP REST][rest],
[https://api.brasil.io/](https://api.brasil.io/), com o objetivo de ser o ponto
de encontro entre quem quer disponibilizar e acessar os dados.


### Colabore

O software por trás da [API HTTP REST][rest] é [livre][sl], desenvolvido de
forma colaborativa, assim como os dados lá disponibilizados.

Caso queira participar do desenvolvimendo do projeto, seja desenvolvendo
código, discutindo deciões, enviando dados etc., fique à vontade para entrar em
nossa lista de e-mails e interagir:
[Brasil-IO no Google Groups][lista-brasilio]. Seja bem-vindo! :-)


## Descrição Técnica

### Tecnologias Utilizadas

- [nginx][nginx] como servidor Web proxy e balanceador de carga;
- [uWSGI][uwsgi] como servidor Web;
- [Python][python] como principal linguagem de programação;
- [Flask][flask] como *framework* para desenvolvimento Web;
- [JSON-LD][jsonld] para representação dos dados.

### Recursos HTTP Disponíveis

Os recursos visam descrever dados sobre o país e, para facilitar o acesso, a
divisão política (unidades federativas e municípios) é utilizada.

Todos os recursos disponíveis possuem suporte a [JSONP][jsonp]
(`?callback=suaFunçãoCallback`) e [CORS][cors] (quando o *header* HTTP `Origin`
está presente), com o objetivo de facilitar a integração com outros
serviços/websites.


#### Regiões

- [/regioes/][regioes]: lista as 5 macrorregiões geográficas do país (5,
  atualmente);
- [/regioes/sudeste/][sudeste]: exemplo de recurso de macrorregião. Possui
  lista de unidades federativas da região, bem como outros possíveis dados que
  usuários queiram disponibilizar.

#### Unidades Federativas

- [/unidades-federativas/][ufs]: lista as unidades federativas do país (27,
  atualmente);
- [/unidades-federativas/rj/][rj]: exemplo de recurso de unidade federativa.
  Possui lista de: mesorregiões, microrregiões e muinicípios, bem como outros
  possíveis dados que usuários queiram disponibilizar;
- [/unidades-federativas/rj/mesorregioes/][rj-meso]: exemplo de coleção de
  mesorregiões de uma unidade federativa;
- [/unidades-federativas/rj/mesorregioes/centro-fluminense/][rj-meso-centro]:
  exemplo de recurso relativo a mesorregião, que deve listar as microrregiões
  contidas nela;
- [/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/][rj-meso-centro-micro]:
  exemplo de coleção de microrregiões, que deve listar os municípios contidos
  nela;
- [/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/tres-rios/][rj-meso-centro-micro-tr]:
  exemplo de recurso de microrregião, que deve listar os municípios contidos
  nela.

#### Recursos Relativos à API

- `/meta/contextos/`: contextos JSON-LD;
- `/usuarios/`: informações sobre usuários cadastrados na API (se feito
  `POST`, cria usuário);
- `/usuarios/turicas/`: informações sobre um usuário.


## A Implementar

- Propriedades devem ser camelCase;
- JSON-LD em vez de JSON;
- Alterar Content-Type (exemplo: `application/vnd+brasil.io.nome-do-schema+json`),
  inclusive para incluir a versão do formato
  (exemplo: `application/vnd+brasil.io.schema.v2+json`);
- Verificar *header* HTTP `Accept` para todas requisições;
- Implementar cadastro de usuários;
- Implementar criação de API Tokens;
- Melhorar suporte a cache (`ETag`, `If-Unmodified-Since` etc.);
- Quando factível, retornar corpo do documento em resposta a POST/PUT/DELETE;


## Questões Em Aberto

- Usar [Hydra](http://www.markus-lanthaler.com/hydra/spec/latest/core/)?
- Como criar novos recursos/coleção de recursos? Qual deve ser a URL dele?
- Como escolher o dado "oficial"?
- Usar ou não usar `/` no final das URLs?
- Utilizar somente `Last-Modified` ou campo dentro do corpo do resultado?
- O que abranger na funcionalidade de busca?
- Devemos suportar marcadores (tags) para os recursos/dados?
- Suportar `?format=jsonld|rdf|csv`?
- Suportar `?expand`, para automaticamente expandir coleções de recursos?
- Quais dados mais importantes para a primeira versão? Rascunho:
  - População
  - Renda do domicílio
  - Área
  - Shapefile
  - IDH
  - PIB
  - Frota
  - Registro Civil
  - Sites oficiais
- Definir propriedades que constarão em cada dado informado. Rascunho:
  - Nome (exemplo: população)
  - Valor (exemplo: 77439)
  - Tipo (exemplo: inteiro)
  - Unidade (exemplo: habitantes)
  - Autor (exemplo: turicas)
  - Fonte (exemplo: IBGE)
  - Versão (exemplo: CENSO2010)
  - Licença (exemplo: "CC-BY-like")
  - Data do envio
  - Data da última modificação

[lai]: http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm

[brasil.io]: http://www.brasil.io/
[rest]: https://en.wikipedia.org/wiki/Representational_state_transfer
[sl]: https://pt.wikipedia.org/wiki/Software_livre
[5starsopendata]: http://5stardata.info/
[lista-brasilio]: https://groups.google.com/forum/#!forum/brasil-io

[nginx]: http://nginx.org/
[uwsgi]: http://projects.unbit.it/uwsgi/
[python]: http://www.python.org/
[flask]: http://flask.pocoo.org/
[jsonld]: http://json-ld.org/

[jsonp]: https://en.wikipedia.org/wiki/JSONP
[cors]: https://en.wikipedia.org/wiki/Cross-origin_resource_sharing

[regioes]: https://api.brasil.io/regioes/
[sudeste]: https://api.brasil.io/regioes/sudeste/
[ufs]: https://api.brasil.io/unidades-federativas/
[rj]: https://api.brasil.io/unidades-federativas/rj/
[rj-meso]: https://api.brasil.io/unidades-federativas/rj/mesorregioes/
[rj-meso-centro]: https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/
[rj-meso-centro-micro]: https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/][rjmesocentromicro
[rj-meso-centro-micro-tr]: https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/tres-rios
