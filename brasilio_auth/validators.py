import re

from disposable_email_domains import blocklist
from django import forms


def normalize_email_address(email: str) -> str:
    """
    Normaliza endereços de email para validação

    - Para Gmail/Googlemail: remove plus-addressing, remove pontos do local-part (Gmail ignora ambos no roteamento) e
      unifica o domínio em gmail.com.
    - Outros domínios: apenas strip + lowercase.
    """
    email = email.strip().lower()
    if "@" not in email:
        return email
    local, _, domain = email.partition("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def is_disposable_email_domain(email: str) -> bool:
    """Verifica se domínio do email está em lista de provedores de email descartáveis

    Testa o domínio inteiro e cada sufixo: `foo@sub.mailinator.com` retorna `True` se `mailinator.com` estiver listado.
    """
    domain = email.partition("@")[2]
    if not domain:
        return False
    partes = domain.split(".")
    while len(partes) > 1:
        if ".".join(partes) in blocklist:
            return True
        partes = partes[1:]
    return False


def validate_email_not_disposable(email: str) -> None:
    if is_disposable_email_domain(email):
        raise forms.ValidationError("Endereço de e-mail inválido.")


# "a" + celular taiwanês (09 + 8 dígitos). Assinatura de fazendas de contas Gmail "aged" revendidas, criadas em massa
# via SMS virtual taiwanês: 5 cadastros nesse formato em 2026-05-14, com ativação por e-mail (a fazenda tem acesso à
# inbox).
PHONE_GMAIL_FARM_PATTERNS = [
    re.compile(r"^a09\d{8}@gmail\.com$", re.IGNORECASE),
]


def validate_email_not_phone_gmail_farm(email: str) -> None:
    if any(padrao.match(email) for padrao in PHONE_GMAIL_FARM_PATTERNS):
        raise forms.ValidationError("Endereço de e-mail inválido.")
