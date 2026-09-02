# Pendências de dados após merge de `fix/normaliza-email-username`

Contexto: app `brasilio_auth`. O branch impede _novas_ colisões de username/e-mail, mas as existentes na base continuam lá (de propósito: apagá-las ou renomeá-las sem decisão seria pior). Este arquivo lista o que ainda exige decisão humana ou automatizada. Para listar os casos reais, rodar:

```
python manage.py audit_email_normalization --only-duplicates          # colisões de e-mail normalizado (apenas ativos)
python manage.py audit_email_normalization --include-inactive -d      # incluir inativos
```

## Usernames que diferem só em maiúsculas/minúsculas

`auth_user.username` tem UNIQUE case-sensitive, então `larraw` e `Larraw` coexistem. Ambos os logins continuam funcionando (o backend testa a senha em cada candidata), mas:
- É vetor de confusão/engenharia social (parecem a mesma pessoa);
- Qualquer migração futura para UNIQUE _case-insensitive_ vai esbarrar neles.

Decisão possível por caso: renomear um dos dois (escolhendo nome próximo, como `larraw_`), contatar o dono da conta, ou desativar a inativa. Não há comando automatizado ainda.

## E-mails idênticos ignorando maiúsculas/espaços

Mesmo e-mail gravado com diferença de caixa/espaços em contas diferentes (`Foo@X.com` vs `foo@x.com`). Sintomas: os dois logam com o próprio e-mail exato, mas notificações vão para a mesma caixa real.

Decisão possível: é provavelmente a mesma pessoa - unificar contas (o script `brasilio_auth/scripts/migrate_duplicate_emails.py` já faz isso para duplicatas exatas em maiúsculas/minúsculas; verificar se cobre trim) ou desativar a mais recente.

## E-mails que colidem só após a normalização (aliases de Gmail)

`foo@gmail.com` e `f.o.o+tag@gmail.com` são a mesma caixa no Gmail, mas contas distintas na base. A mais antiga/ativa tem `NormalizedEmail`; a outra não tem e não terá enquanto não houver decisão.

Sintomas: a conta sem linha não loga por alias e não pode trocar o e-mail sem passar por decisão manual (o `pre_save` barra).

Decisão possível por caso: desativar a conta duplicada (criada por erro ou por bot), renomear o e-mail dela (ex.: adicionar sufixo), ou contatar o usuário.

## Usuários sem `NormalizedEmail` por colisão no _backfill_

Resultado esperado do backfill (em `0004_backfill_normalized_email.py`): em cada grupo de colisão, só o usuário ativo mais antigo ganhou linha. Todos os outros do grupo ficam sem - é o estado "conta legada". Não é bug, mas são os mesmos casos dos itens 2 e 3, esperando resolução.

## Constraint de unicidade no banco

Com a base limpa, podemos levar o e-mail normalizado para a própria tabela de usuário com UNIQUE, eliminando a corrida que hoje é tratada com `IntegrityError` em `brasilio_auth/signals.py`. _Trade-offs_ a decidir:

- `auth_user` é a tabela do `django.contrib.auth`: adicionar coluna exige migração personalizada (`RunSQL`) ou trocar `AUTH_USER_MODEL`.
- Se for coluna _gerada_ (`GENERATED ALWAYS AS (...) STORED`), a normalização precisa existir também em SQL (remover pontos/plus do Gmail etc.), duplicando a regra de `validators.normalize_email_address` - risco de divergência entre as duas implementações (evitar).
- Alternativa mais simples: manter a tabela `NormalizedEmail` e apenas confiar no `IntegrityError` já tratado, aceitando o estado residual raro (duas contas, uma com linha) como documentado no comentário do signal.
