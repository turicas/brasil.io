from brasilio_auth.validators import normalize_email_address


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
