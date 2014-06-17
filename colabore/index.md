---
layout: page
title: Colabore
---

# Colabore

O software por trás da [API HTTP
REST](https://en.wikipedia.org/wiki/Representational_state_transfer) é
[livre](https://pt.wikipedia.org/wiki/Software_livre), está sendo desenvolvido
de forma colaborativa, assim como os dados lá disponibilizados serão.

Caso queira colaborar com o desenvolvimendo do projeto, seja desenvolvendo
código, discutindo decisões, enviando dados etc., fique à vontade para
interagir conosco através dos seguintes meios:

- [Repositório de código no GitHub](https://github.com/turicas/api.brasil.io/)
- [Lista de e-mails Brasil-IO no Google Groups](https://groups.google.com/forum/#!forum/brasil-io)
- [Twitter @brasil_io](https://twitter.com/brasil_io)
- [Canal #Brasil.IO em irc.FreeNode.net.](http://webchat.freenode.net/?channels=#Brasil.IO)


## A Implementar

- Propriedades devem ser camelCase, que é o padrão do JavaScript (e,
  consequentemente, do JSON)
- Usar JSON-LD em vez de JSON Alterar Content-Type (exemplo:
  application/vnd+brasil.io.nome-do-schema+json), inclusive para incluir a
  versão do formato (exemplo: application/vnd+brasil.io.schema.v2+json)
- Verificar header HTTP Accept para todas requisições e responder de acordo
  (caso o cliente não suporte o tipo de conteúdo que seria retornado)
- Implementar cadastro de usuários
- Implementar criação de API tokens Melhorar suporte a cache (ETag,
  If-Unmodified-Since etc.)
- Quando factível, retornar corpo do documento em resposta a POST/PUT/DELETE


## Possíveis Fontes de Dados

As fontes de dados abaixo poderão ser utilizadas por desenvolvedores de
software com a finalidade de capturar, limpar e padronizar os dados, ficando
estes prontos para serem submetidos à API do Brasil.IO:

- [Instituto Brasileiro de Geografia e Estatística](http://www.ibge.gov.br/)
- [Programa das Nações Unidas para o Desenvolvimento](http://www.pnud.org.br/)
- [ONG Transparência](http://www.transparencia.org.br/)
- [Dados.GOV.BR](http://dados.gov.br/)
- [Instituto de Pesquisa Econômica Aplicada](http://www.ipea.gov.br/)
