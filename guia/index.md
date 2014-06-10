---
layout: page
title: Guia
---

# Guia

## Recursos HTTP Disponíveis

Os recursos visam descrever dados sobre o país e, para facilitar o acesso, a
divisão política (unidades federativas e municípios) é utilizada.

Todos os recursos possuem suporte a
[JSONP](https://en.wikipedia.org/wiki/JSONP) (?callback=suaFunçãoCallback) e
[CORS](https://en.wikipedia.org/wiki/Cross-origin_resource_sharing) (quando o
header HTTP Origin está presente), com o objetivo de facilitar a integração com
outros serviços/websites.

Por questões de segurança, a API aceita apenas requisições via
[HTTPS](https://en.wikipedia.org/wiki/HTTP_Secure).

Os recursos a seguir ainda não estão totalmente disponíveis, visto que a API
está em fase inicial de desenvolvimento -- são apenas uma especificação para
facilitar o desenvolvimento de novas funcionalidades.

## Regiões

**[/regioes/](https://api.brasil.io/regioes/)** - lista as 5 macrorregiões
geográficas do país (5, atualmente)

**[/regioes/sudeste/](https://api.brasil.io/regioes/sudeste/)** - exemplo de
recurso de macrorregião. Possui lista de unidades federativas da região, bem
como outros possíveis dados que usuários queiram disponibilizar.

## Unidades Federativas
**[/unidades-federativas/](https://api.brasil.io/unidades-federativas/)** -
lista as unidades federativas do país (27, atualmente).

**[/unidades-federativas/rj/](https://api.brasil.io/unidades-federativas/rj/)**
- exemplo de recurso de unidade federativa. Possui lista de: mesorregiões,
microrregiões e municípios, bem como outros possíveis dados que usuários
queiram disponibilizar.

**[/unidades-federativas/rj/mesorregioes/](https://api.brasil.io/unidades-federativas/rj/mesorregioes/)**
- exemplo de coleção de mesorregiões de uma unidade federativa.

**[/unidades-federativas/rj/mesorregioes/centro-fluminense/](https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/)**
- exemplo de recurso relativo a mesorregião, que deve listar as microrregiões
contidas nela.

**[/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/](https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/][rjmesocentromicro)**
-  exemplo de coleção de microrregiões, que deve listar os municípios contidos
nela.

**[/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/tres-rios/](https://api.brasil.io/unidades-federativas/rj/mesorregioes/centro-fluminense/microrregioes/tres-rios)**
- exemplo de recurso de microrregião, que deve listar os municípios contidos
nela.

## Recursos Relativos à API

- `/meta/schemas/`: schemas de dados disponíveis.
- `/meta/contexts/`: contextos JSON-LD.
- `/users/`: usuários cadastrados na API.
- `/users/turicas/`: informações sobre um determinado usuário.
