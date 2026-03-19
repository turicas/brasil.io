from unittest.mock import patch

import pytest
from django.core.mail.message import EmailMessage

from core.forms import ContactForm, sanitizar_nome_para_email, validar_mensagem_contato, validar_texto_sem_html


@pytest.fixture(autouse=True)
def _mock_captcha():
    with patch("utils.forms.FlagedReCaptchaField.validate", return_value=None):
        yield


def _form_valido(**overrides):
    data = {
        "name": "João Silva",
        "email": "joao@example.com",
        "message": "Olá, gostaria de saber mais sobre o projeto.",
        "g-recaptcha-response": "PASSED",
    }
    data.update(overrides)
    return data


def test_texto_sem_html_valido():
    assert validar_texto_sem_html("Olá, tudo bem?", "campo") == "Olá, tudo bem?"


def test_texto_sem_html_com_tag_a():
    with pytest.raises(Exception, match="O campo campo_x não pode conter HTML."):
        validar_texto_sem_html('<a href="https://vk.com">spam</a>', "campo_x")


def test_texto_sem_html_com_tag_script():
    with pytest.raises(Exception, match="O campo campo_y não pode conter HTML."):
        validar_texto_sem_html("texto <script>alert(1)</script>", "campo_y")


def test_texto_sem_html_com_tag_img():
    with pytest.raises(Exception, match="O campo campo_z não pode conter HTML."):
        validar_texto_sem_html('<img src="x" onerror="alert(1)">', "campo_z")


def test_mensagem_valida_simples():
    assert validar_mensagem_contato("Olá, gostaria de saber mais.") == "Olá, gostaria de saber mais."


def test_mensagem_valida_com_acentos():
    msg = "Não recebi o e-mail de confirmação. Poderiam verificar?"
    assert validar_mensagem_contato(msg) == msg


def test_mensagem_valida_com_uma_url():
    msg = "Esse link não funciona: https://brasil.io/datasets"
    assert validar_mensagem_contato(msg) == msg


def test_mensagem_valida_com_duas_urls():
    msg = "Links: https://brasil.io/a e https://brasil.io/b"
    assert validar_mensagem_contato(msg) == msg


def test_mensagem_vazia():
    with pytest.raises(Exception, match="obrigatória"):
        validar_mensagem_contato("")


def test_mensagem_somente_espacos():
    with pytest.raises(Exception, match="obrigatória"):
        validar_mensagem_contato("   ")


def test_mensagem_com_html():
    with pytest.raises(Exception, match="O campo mensagem não pode conter HTML."):
        validar_mensagem_contato('<a href="https://t.me/spam">clique</a>')


def test_mensagem_com_html_sem_href():
    with pytest.raises(Exception, match="O campo mensagem não pode conter HTML."):
        validar_mensagem_contato("texto <b>negrito</b> texto")


def test_mensagem_com_cirilico():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Современные решения в сфере логистики")


def test_mensagem_com_cirilico_misturado():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Hello! Продвижение сайта по регионам")


def test_mensagem_com_arabe():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("مرحبا بالعالم")


def test_mensagem_com_chines():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("你好世界")


def test_mensagem_com_japones():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("こんにちは世界")


def test_mensagem_com_coreano():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("안녕하세요")


def test_nome_com_cirilico():
    form = ContactForm(data=_form_valido(name="Buddyevins"))
    assert form.is_valid()  # nome latin é ok

    form = ContactForm(data=_form_valido(name="Владимир"))
    assert not form.is_valid()
    assert "name" in form.errors


def test_mensagem_com_tinyurl():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Spin to Win Here -> tinyurl.com/23s4sswk")


def test_mensagem_com_bitly():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Clique aqui: https://bit.ly/abc123")


def test_mensagem_com_isgd():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Start Spinning Here => is.gd/TwtFdU")


def test_mensagem_com_uto():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Your turn starts now! u.to/qsA6Ig")


def test_mensagem_com_pseeio():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Claim your prize! psee.io/8r5ffm")


def test_mensagem_com_hopcx():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Appreciation you. https://hop.cx")


def test_mensagem_url_normal_nao_bloqueia():
    msg = "A página https://brasil.io/datasets não está funcionando."
    assert validar_mensagem_contato(msg) == msg


def test_mensagem_com_bbcode_url():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("Прогон хрумером [url=https://ru.xelo.pro/]link[/url]")


def test_mensagem_com_bbcode_img():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("[img]https://example.com/foto.jpg[/img]")


def test_mensagem_com_bbcode_color():
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato("[color=red]texto[/color]")


def test_mensagem_com_tres_urls():
    msg = "Links: https://a.com https://b.com https://c.com"
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato(msg)


def test_mensagem_com_muitas_urls_spam_russo():
    msg = (
        "Продвижение https://proffseo.ru/ " "SEO https://proffseo.ru/kontakty " "Результаты https://proffseo.ru/privacy"
    )
    with pytest.raises(Exception, match="Sua mensagem foi bloqueada pelo filtro anti-SPAM."):
        validar_mensagem_contato(msg)


def test_mensagem_spam_urls_latinas():
    msg = "Важная информация " "https://site1.ru/ https://site2.ru/page " "https://site3.ru/other https://site4.ru/more"
    with pytest.raises(Exception):
        validar_mensagem_contato(msg)


def test_form_valido():
    form = ContactForm(data=_form_valido())
    assert form.is_valid(), form.errors


def test_form_mensagem_legitima_com_url():
    form = ContactForm(data=_form_valido(message="O link https://brasil.io/especiais não abre."))
    assert form.is_valid(), form.errors


def test_form_nome_com_html_invalido():
    form = ContactForm(data=_form_valido(name='<a href="https://vk.com/promokody">promokodwtOi</a>'))
    assert not form.is_valid()
    assert "name" in form.errors


def test_form_mensagem_com_html_invalida():
    form = ContactForm(data=_form_valido(message='<a href="https://t.me/spam">промокоды</a>'))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_mensagem_cirilico_puro():
    form = ContactForm(data=_form_valido(message="Оборудование для производства"))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_mensagem_url_encurtada():
    form = ContactForm(data=_form_valido(message="Win big! tinyurl.com/abc123"))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_mensagem_bbcode():
    form = ContactForm(data=_form_valido(message="[url=https://spam.com]click[/url]"))
    assert not form.is_valid()
    assert "message" in form.errors


def test_form_mensagem_muitas_urls():
    msg = "Veja: https://a.com e https://b.com e https://c.com"
    form = ContactForm(data=_form_valido(message=msg))
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


def test_spam_original_caso_1():
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


def test_spam_original_caso_2():
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


def test_spam_jsonl_cirilico_russo():
    form = ContactForm(
        data=_form_valido(
            name="Buddyevins",
            email="dolnovam@mail.ru",
            message="Выйдите на новые рынки — продвижение по России https://proffseo.ru/",
        )
    )
    assert not form.is_valid()
    assert "message" in form.errors


def test_spam_jsonl_tinyurl_gambling():
    form = ContactForm(
        data=_form_valido(
            name="Dwane4m",
            email="julio4i5o@zohomail.eu",
            message="Why wait? 1M is waiting on Mega Slots. Spin to Win Here -> tinyurl.com/23s4sswk",
        )
    )
    assert not form.is_valid()
    assert "message" in form.errors


def test_spam_jsonl_isgd():
    form = ContactForm(
        data=_form_valido(
            name="Eskerpl",
            email="marioepcz@aol.com",
            message="The truth: 1 in 5 spins pays a jackpot. Test it! Start Spinning Here => is.gd/TwtFdU",
        )
    )
    assert not form.is_valid()
    assert "message" in form.errors


def test_spam_jsonl_muitas_urls():
    form = ContactForm(
        data=_form_valido(
            name="Charlesfah",
            email="test@mail.ru",
            message=(
                "https://www.kondhp.ru/preorder/12797 "
                "https://www.kondhp.ru/preorder/12860 "
                "https://www.kondhp.ru/preorder/12854"
            ),
        )
    )
    assert not form.is_valid()
    assert "message" in form.errors


def test_spam_jsonl_bbcode():
    form = ContactForm(
        data=_form_valido(
            name="XeloDype",
            email="a@xelo.pro",
            message="Продвижение сайта: [url=https://ru.xelo.pro/]Прогон хрумером[/url]",
        )
    )
    assert not form.is_valid()
    assert "message" in form.errors


def test_legit_confirmacao_cadastro():
    form = ContactForm(
        data=_form_valido(
            name="João Carlos Silva",
            email="joao_carlos_silva@example.com",
            message="Olá, fiz o cadastro na plataforma, porém, não recebo o e-mail de ativação. Como devo proceder?",
        )
    )
    assert form.is_valid(), form.errors


def test_sanitizar_nome_limpo():
    assert sanitizar_nome_para_email("João Silva") == "João Silva"


def test_sanitizar_nome_com_html():
    resultado = sanitizar_nome_para_email('<a href="https://vk.com/promokody">promokodwtOi</a>')
    assert "<" not in resultado
    assert ">" not in resultado
    assert resultado == "promokodwtOi"


def test_sanitizar_nome_vazio_apos_limpeza():
    assert sanitizar_nome_para_email('<a href="https://example.com"></a>') == ""


def test_email_message_com_nome_sanitizado_de_spam():
    nome_seguro = sanitizar_nome_para_email('<a href="https://vk.com/promokody">promokodwtOi</a>')
    email = EmailMessage(
        subject=f"Contato no Brasil.IO: {nome_seguro}",
        body="Mensagem de teste.",
        from_email=f"{nome_seguro} (via Brasil.IO) <contato@brasil.io>",
        to=["contato@brasil.io"],
        reply_to=[f"{nome_seguro} <spam@example.com>"],
    )
    msg = email.message()
    assert "contato@brasil.io" in msg["From"]
