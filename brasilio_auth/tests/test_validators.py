import pytest
from django import forms

from brasilio_auth.validators import is_disposable_email_domain, normalize_email_address, validate_email_not_disposable


class TestNormalizeEmailAddress:
    def test_minusculas_e_strip_para_dominio_qualquer(self):
        assert "foo@example.com" == normalize_email_address("  FOO@Example.COM  ")

    def test_remove_plus_addressing_do_gmail(self):
        assert "foo@gmail.com" == normalize_email_address("foo+qualquer-coisa@gmail.com")

    def test_remove_pontos_do_username_do_gmail(self):
        assert "foobar@gmail.com" == normalize_email_address("foo.bar@gmail.com")

    def test_unifica_googlemail_em_gmail(self):
        assert "foo@gmail.com" == normalize_email_address("foo@googlemail.com")

    def test_aplicacao_combinada_dos_tres(self):
        assert "foobar@gmail.com" == normalize_email_address("FOO.BAR+tag@GoogleMail.com")

    def test_dominio_nao_gmail_nao_remove_pontos_nem_mais(self):
        assert "foo.bar+tag@example.com" == normalize_email_address("foo.bar+tag@example.com")

    def test_endereco_sem_arroba_retorna_em_minusculas_e_sem_espacos(self):
        assert "naoeumemail" == normalize_email_address("  NaoEumEmail  ")

    def test_endereco_vazio_retorna_string_vazia(self):
        assert "" == normalize_email_address("")


class TestDisposableEmailDomain:
    def test_is_disposable_pega_dominio_de_topo(self):
        assert is_disposable_email_domain("foo@mailinator.com") is True
        with pytest.raises(forms.ValidationError) as exc_info:
            validate_email_not_disposable("foo@mailinator.com")
        assert ["Endereço de e-mail inválido."] == exc_info.value.messages

    def test_is_disposable_pega_subdominio(self):
        assert is_disposable_email_domain("foo@sub.mailinator.com") is True

    def test_is_disposable_nao_pega_dominio_legitimo(self):
        assert is_disposable_email_domain("foo@gmail.com") is False
        assert validate_email_not_disposable("foo@gmail.com") is None
