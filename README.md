# Brasil.IO - Dados abertos para um Brasil mais ligado

![Django CI](https://github.com/turicas/brasil.io/workflows/Django%20CI/badge.svg)

### O Problema

Muitos dados públicos brasileiros estão disponíveis (principalmente depois da
criação da Lei de Acesso à Informação), mas não necessariamente acessíveis.
Mesmo que a informação esteja disponível, nem sempre ela está disponível em um
formato legível por máquina, ou utilizando um formato aberto, ou possui
descrição (metadados) que facilitem a interpretação (manual ou automática)
desses dados. **Quanto menos acessível é uma informação, mais perto de ser
fechada ela está**.

Além do problema relativo à acessibilidade, não existe um lugar comum em que
todos os dados disponíveis estejam organizados e catalogados, dificultando
ainda mais o acesso (ou a descoberta que esse tipo de informação está
disponível).

O objetivo do projeto não é concorrer com iniciativas correlatas do Governo
(como o dados.gov.br) e de outras organizações -- pelo contrário, gostaríamos
de disponibilizar os dados que essas organizações já disponibilizam, porém de
forma integrada e estruturada, permitindo a qualquer um (independente de
vínculo) possa disponibilizar dados, independente da fonte.


### A Solução

O projeto Brasil.IO foi criado com o objetivo de ser referência para quem
procura ou quer publicar dados abertos sobre o Brasil de forma organizada,
legível por máquina e usando padrões abertos. O projeto foi idealizado e está
sendo desenvolvido por Álvaro Justen, com a colaboração de outros
desenvolvedores.


### Colabore

[![Entre em contato com o Brasil.IO por chat!](docs/chat-banner.png)](https://chat.brasil.io/)

Temos alguns documentos com instruções para te ajudar a colaborar com o projeto:

- Veja [docs/dev-setup.md](docs/dev-setup.md) para configurar o projeto na sua máquina;
- Veja [docs/import-data.md](docs/import-data.md) para importar os dados dos [diversos datasets](https://brasil.io/datasets/) do Brasil.io;
- Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes sobre como montar seu pull request;

## Deployment no Dokku

Veja [docs/deploy-dokku.md](docs/deploy-dokku.md).


### Licença

[GNU General Public License version 3](https://www.gnu.org/licenses/gpl.html)
