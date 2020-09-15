# Importando os dados

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

**IMPORTANTE**: o comando `import_data` não irá funcionar caso você não tenha executado o comando `python manage.py update_data`.

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


