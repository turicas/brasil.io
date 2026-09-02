from django.contrib.auth import get_user_model
from model_bakery import baker


def criar_conta_legada(**campos):
    """
    Cria uma conta que colide em username/e-mail com outra já existente, como as anteriores à checagem de unicidade.

    Passa por `update()` para não disparar o `pre_save` que impede novas colisões nem o `post_save` que cria
    `NormalizedEmail` (contas legadas em colisão não têm um).
    """
    User = get_user_model()
    user = baker.make(User, **{campo: valor for campo, valor in campos.items() if campo not in ("username", "email")})
    User.objects.filter(pk=user.pk).update(
        **{campo: campos[campo] for campo in ("username", "email") if campo in campos}
    )
    user.refresh_from_db()
    return user
