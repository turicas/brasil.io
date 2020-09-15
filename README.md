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
- Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes sobre como montar seu pull request;

Para importar alguma base de dados para rodar no sistema é necessário o baixar
o dump
[aqui](https://drive.google.com/drive/u/0/folders/1yJyDFbTfX8w3uEJ9mTIN3Jow5TvJsYo7).

Alguns arquivos demoram bastante para serem importados, pois são muito grandes.
Um exemplo de arquivo menor é o dataset
[cursos-prouni](https://drive.google.com/open?id=1mlqNGmUe7i8RC1rSPCBZAfBFD3SO6B70).

Após fazer o download do arquivo basta executar o seguinte comando:

```bash
python manage.py import_data --no-input cursos-prouni cursos cursos-prouni.csv.xz
```

> Nota 1: caso queira importar diversos datasets, crie um diretório `data`,
> coloque lá os diretórios de dados existentes no Google Drive e execute o
> arquivo [scripts/import-datasets.sh](scripts/import-datasets.sh), que
> executará todos os `import_data`.

> Nota 2: você pode baixar um arquivo grande e importar somente parte dele para
> que o processo não demore muito. Para isso, basta descompactar o CSV e
> criar um novo arquivo com menos linhas, exemplo:
> `xzcat socios.csv.xz | head -10000 | xz -z > socios-10k.csv.xz`. Essa dica é
> particularmente útil para você ter o sistema todo funcionando (como as
> páginas especiais, que dependem de diversos datasets).

O comando `import_data` irá executar as seguintes operações:

- Deletar a tabela que contém os dados
  (`data_cursosprouni_cursos`), caso exista;
- Criar uma nova tabela, usando os metadados sobre ela que estão em `Table` e
  `Field`;
- Criar um gatilho no PostgreSQL para preenchimento automático do índice de
  busca de texto completo;
- Importar os dados do CSV usando
  [`rows.utils.pgimport`](https://github.com/turicas/rows/blob/develop/rows/utils.py#L580)
  (que usa o comando COPY da interface de linha de comando `psql`);
- Rodar o comando SQL `VACUUM ANALYSE` para que o PostgreSQL preencha
  estatísticas sobre a tabela (isso ajudará a melhorar o desempenho de diversas
  consultas);
- Criar os índices em campos que estão marcados como possíveis de serem usados
  como filtros na interface, para otimizar a busca;
- Preencher um cache em `Field` contendo todas as possíveis opções para os
  campos que estão marcados como "choiceable" (são os campos filtráveis e que
  possuem poucas opções de valor, como unidade federativa, ano etc.).

> Nota 1: você pode pular algumas das etapas acima passando as opções
> `--no-xxx` para o comando.

> Nota 2: em um computador moderno (Intel(R) Core(TM) i7-7500U CPU @ 2.70GHz,
> 16GB RAM e SSD) os dados costumam demorar entre 2.3 a 2.7MB/s para serem
> importados completamente (esse valor é o do dado descompactado).


## Deployment no Dokku

Veja [deploy-dokku.md](deploy-dokku.md).


### Licença

[GNU General Public License version 3](https://www.gnu.org/licenses/gpl.html)
