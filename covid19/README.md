# COVID-19

Esse app Django contém o sistema de atualização de dados da COVID-19 pelas
pessoas voluntárias.


## Atualizando lista de pessoas voluntárias

- Baixar planilha em formato XLSX com contatos (interna)
- Executar:

```shell
python manage.py runscript atualiza_voluntarios --script-args arquivo.xlsx
```
Os dados da planilha (folhas "Contatos" e "ex-voluntarios") serão convertidos
para o JSON usado no backend e enviados a `data.brasil.io`.
