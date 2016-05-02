# Brasil.IO - Dados Abertos Sem Burocracia

# `api.brasil.io`

![Logotipo Brasil.IO](https://pbs.twimg.com/profile_images/449683154316435456/vVZi4P2o.png)

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

Está sendo desenvolvida uma [API HTTP REST][rest],
[https://api.brasil.io/](https://api.brasil.io/), com o objetivo de ser o ponto
de encontro entre quem quer disponibilizar e acessar os dados. Caso queira
colaborar com o desenvolvimento, acesse:
<https://github.com/turicas/api.brasil.io/>.

A API **ainda não está funcional**! O projeto será lançado durante o [15° Fórum
Internacional de Software Livre](http://softwarelivre.org/fisl15), que
acontecerá de 7 a 10 de maio em Porto Alegre/RS.


#### Nota

O objetivo do projeto não é concorrer com iniciativas correlatas do Governo
(como o [dados.gov.br](http://dados.gov.br/)) e de outras organizações -- pelo
contrário, gostaríamos de disponibilizar os dados que essas organizações já
disponibilizam, porém de forma integrada e estruturada, permitindo a qualquer
um (independente de vínculo) possa disponibilizar dados, independente da fonte.


### Colabore

O software por trás da [API HTTP REST][rest] é [livre][sl], está sendo
desenvolvido de forma colaborativa, assim como os dados lá disponibilizados
serão.

Caso queira colaborar com o desenvolvimendo do projeto, seja desenvolvendo
código, discutindo decisões, enviando dados etc., fique à vontade para
interagir conosco através dos seguintes meios:

- [Repositório de código no GitHub](https://github.com/turicas/api.brasil.io/);
- [Lista de e-mails Brasil-IO no Google Groups][lista-brasilio];
- [Twitter @brasil_io][tw-brio];
- [Canal #Brasil.IO em irc.FreeNode.net](http://webchat.freenode.net/?channels=#Brasil.IO).

Seja bem-vindo! :-)


### Quem

O projeto foi idealizado e está sendo desenvolvido por
[Álvaro Justen][turicas], com a colaboração de diversos outros
desenvolvedores.


## Descrição Técnica

### Tecnologias Utilizadas

- [nginx][nginx] como servidor Web proxy e balanceador de carga;
- [uWSGI][uwsgi] como servidor Web;
- [Python][python] como principal linguagem de programação;
- [Flask][flask] como *framework* para desenvolvimento Web;
- [JSON-Schema][json-schema] para validação do tipo de dados;
- [JSON-LD][jsonld] para representação dos dados.


### Recursos HTTP Disponíveis

Os recursos visam descrever dados sobre o país e, para facilitar o acesso, a
divisão política (unidades federativas e municípios) é utilizada.

Todos os recursos possuem suporte a [JSONP][jsonp]
(`?callback=suaFunçãoCallback`) e [CORS][cors] (quando o *header* HTTP `Origin`
está presente), com o objetivo de facilitar a integração com outros
serviços/websites.

Por questões de segurança, a API aceita apenas requisições via
[HTTPS][https-wp].

Os recursos a seguir **ainda não estão totalmente disponíveis**, visto que a
API está em fase inicial de desenvolvimento -- são apenas uma especificação
para facilitar o desenvolvimento de novas funcionalidades.

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
  Possui lista de: mesorregiões, microrregiões e municípios, bem como outros
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

- `/meta/schemas/`: *schemas* de dados disponíveis;
- `/meta/contexts/`: contextos JSON-LD;
- `/users/`: usuários cadastrados na API;
- `/users/turicas/`: informações sobre um determinado usuário.


## A Implementar

- Propriedades devem ser camelCase, que é o padrão do JavaScript (e,
  consequentemente, do JSON);
- Usar JSON-LD em vez de JSON;
- Alterar Content-Type (exemplo: `application/vnd+brasil.io.nome-do-schema+json`),
  inclusive para incluir a versão do formato
  (exemplo: `application/vnd+brasil.io.schema.v2+json`);
- Verificar *header* HTTP `Accept` para todas requisições e responder de acordo
  (caso o cliente não suporte o tipo de conteúdo que seria retornado);
- Implementar cadastro de usuários;
- Implementar criação de API *tokens*;
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

## Possíveis Fontes de Dados

As fontes de dados abaixo poderão ser utilizadas por desenvolvedores de
software com a finalidade de capturar, limpar e padronizar os dados, ficando
estes prontos para serem submetidos à API do Brasil.IO:

- [Instituto Brasileiro de Geografia e Estatística](http://www.ibge.gov.br/)
- [Programa das Nações Unidas para o Desenvolvimento](http://www.pnud.org.br/)
- [ONG Transparência](http://www.transparencia.org.br/)
- [Dados.GOV.BR](http://dados.gov.br/)
- [Instituto de Pesquisa Econômica Aplicada](http://www.ipea.gov.br/)


## Projetos Afins

- [Olho Neles](http://olhoneles.org/)
- [Politicando](http://politicando.org/)
- [TeleMob](http://telemob.com.br/)
- [WorldBank Data](http://data.worldbank.org/)
- [Quandl](http://www.quandl.com/)


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
[json-schema]: http://json-schema.org/

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

[https-wp]: https://en.wikipedia.org/wiki/HTTP_Secure
[turicas]: https://twitter.com/turicas
[tw-brio]: https://twitter.com/brasil_io
