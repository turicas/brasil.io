from unittest.mock import patch

import pytest
from django.core.mail.message import EmailMessage

from core.forms import (
    RE_CARACTERES_INVALIDOS_NOME,
    RE_HTML_TAG,
    ContactForm,
    sanitizar_nome_para_email,
    validar_texto_sem_html,
)


def test_texto_sem_html_valido():
    assert validar_texto_sem_html("Olá, tudo bem?", "campo") == "Olá, tudo bem?"


def test_texto_sem_html_com_espacos_extras():
    assert validar_texto_sem_html("  texto  ", "campo") == "texto"


def test_texto_sem_html_com_tag_a():
    with pytest.raises(Exception, match="HTML"):
        validar_texto_sem_html('<a href="https://vk.com">spam</a>', "campo")


def test_texto_sem_html_com_tag_script():
    with pytest.raises(Exception, match="HTML"):
        validar_texto_sem_html("texto <script>alert(1)</script>", "campo")


def test_texto_sem_html_com_tag_img():
    with pytest.raises(Exception, match="HTML"):
        validar_texto_sem_html('<img src="x" onerror="alert(1)">', "campo")


def test_nome_valido_simples():
    assert not RE_HTML_TAG.search("João Silva")
    assert not RE_CARACTERES_INVALIDOS_NOME.search("João Silva")


def test_nome_valido_com_hifen():
    assert not RE_HTML_TAG.search("José María López-García")
    assert not RE_CARACTERES_INVALIDOS_NOME.search("José María López-García")


def test_nome_com_tag_html():
    assert RE_HTML_TAG.search('<a href="https://vk.com/promokody_segodnya">promokodwtOi</a>')


def test_nome_com_menor_que():
    assert RE_CARACTERES_INVALIDOS_NOME.search("nome < sobrenome")


def test_nome_com_maior_que():
    assert RE_CARACTERES_INVALIDOS_NOME.search("nome > sobrenome")


def test_nome_com_aspas_duplas():
    assert RE_CARACTERES_INVALIDOS_NOME.search('nome "apelido" sobrenome')


def test_nome_com_barra_invertida():
    assert RE_CARACTERES_INVALIDOS_NOME.search("nome\\sobrenome")


def test_nome_com_caractere_controle():
    assert RE_CARACTERES_INVALIDOS_NOME.search("nome\x00sobrenome")


def test_sanitizar_nome_limpo():
    assert sanitizar_nome_para_email("João Silva") == "João Silva"


def test_sanitizar_nome_com_html():
    resultado = sanitizar_nome_para_email('<a href="https://vk.com/promokody_segodnya">promokodwtOi</a>')
    assert "<" not in resultado
    assert ">" not in resultado
    assert resultado == "promokodwtOi"


def test_sanitizar_nome_com_multiplas_tags():
    assert sanitizar_nome_para_email("<b>Nome</b> <i>Sobrenome</i>") == "Nome Sobrenome"


def test_sanitizar_nome_vazio_apos_limpeza():
    assert sanitizar_nome_para_email('<a href="https://example.com"></a>') == ""


def test_sanitizar_nome_com_aspas():
    resultado = sanitizar_nome_para_email('"Nome"')
    assert '"' not in resultado


def test_sanitizar_nome_com_caracteres_controle():
    resultado = sanitizar_nome_para_email("Nome\x00\x01Sobrenome")
    assert "\x00" not in resultado
    assert "\x01" not in resultado


def _form_valido(**overrides):
    data = {
        "name": "João Silva",
        "email": "joao@example.com",
        "message": "Olá, gostaria de saber mais sobre o projeto.",
        "g-recaptcha-response": "PASSED",
    }
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def _mock_captcha():
    with patch("utils.forms.FlagedReCaptchaField.validate", return_value=None):
        yield


def test_form_valido():
    form = ContactForm(data=_form_valido())
    assert form.is_valid(), form.errors


def test_form_nome_com_html_invalido():
    form = ContactForm(data=_form_valido(name='<a href="https://vk.com/promokody_segodnya">promokodwtOi</a>'))
    assert not form.is_valid()
    assert "name" in form.errors


def test_form_nome_com_menor_que():
    form = ContactForm(data=_form_valido(name="nome < sobrenome"))
    assert not form.is_valid()
    assert "name" in form.errors


def test_form_mensagem_com_html_invalida():
    form = ContactForm(data=_form_valido(message='<a href="https://t.me/promokod_segodnya">промокоды</a>'))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_email_invalido():
    form = ContactForm(data=_form_valido(email="nao-eh-email"))
    assert not form.is_valid()
    assert "email" in form.errors


def test_form_nome_vazio():
    form = ContactForm(data=_form_valido(name=""))
    assert not form.is_valid()
    assert "name" in form.errors


def test_form_mensagem_vazia():
    form = ContactForm(data=_form_valido(message=""))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_nome_muito_longo():
    form = ContactForm(data=_form_valido(name="A" * 201))
    assert not form.is_valid()
    assert "name" in form.errors


def test_reproduz_spam_caso_1_form_rejeita():
    form = ContactForm(
        data=_form_valido(
            name='<a href="https://vk.com/promokody_segodnya">promokodwtOi</a>',
            email="a.u.8834386@gmail.com",
            message='<a href="https://t.me/promokod_segodnya">промокоды на сегодня</a>',
        )
    )
    assert not form.is_valid()
    assert "name" in form.errors
    assert "message" in form.errors


def test_reproduz_spam_caso_2_form_rejeita():
    form = ContactForm(
        data=_form_valido(
            name='<a href="https://vk.com/promokody_segodnya">promokodegOi</a>',
            email="a.u.8834386@gmail.com",
            message='<a href="https://t.me/promokod_segodnya">промокоды сегодня</a>',
        )
    )
    assert not form.is_valid()
    assert "name" in form.errors
    assert "message" in form.errors


def test_email_message_com_nome_limpo():
    nome = "João Silva"
    email = EmailMessage(
        subject=f"Contato no Brasil.IO: {nome}",
        body="Mensagem de teste.",
        from_email=f"{nome} (via Brasil.IO) <contato@brasil.io>",
        to=["contato@brasil.io"],
        reply_to=[f"{nome} <joao@example.com>"],
    )
    msg = email.message()
    assert "contato@brasil.io" in msg["From"]


def test_email_message_com_nome_sanitizado_de_spam():
    nome_original = '<a href="https://vk.com/promokody_segodnya">promokodwtOi</a>'
    nome_seguro = sanitizar_nome_para_email(nome_original)
    assert nome_seguro == "promokodwtOi"
    email = EmailMessage(
        subject=f"Contato no Brasil.IO: {nome_seguro}",
        body="Mensagem de teste.",
        from_email=f"{nome_seguro} (via Brasil.IO) <contato@brasil.io>",
        to=["contato@brasil.io"],
        reply_to=[f"{nome_seguro} <spam@example.com>"],
    )
    msg = email.message()
    assert "contato@brasil.io" in msg["From"]


def test_sanitizacao_vazia_impede_envio():
    nome_original = '<a href="https://example.com"></a>'
    nome_seguro = sanitizar_nome_para_email(nome_original)
    assert nome_seguro == ""
