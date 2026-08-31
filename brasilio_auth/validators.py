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
