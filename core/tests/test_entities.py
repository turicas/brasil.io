from core.entities import Company, Person

# TODO: test Entity

EXPECTED_BASE_URL = "https://uuid.brasil.io"


def test_Person():
    name = "Álvaro Justen"
    document = "***456789**"
    expected_object_id = "456789ALVARO"
    expected_title = f"Pessoa {name}"
    data = {"nome": name, "cpf": document}

    assert Person.base_url == EXPECTED_BASE_URL
    person = Person(data)
    assert person.entity_type == "person"
    assert person.version == 1
    assert person.name == name
    assert person.object_id == expected_object_id
    assert person.document == document
    assert person.title == expected_title


def test_Person_empty_name():
    name = ""
    document = "***456789**"
    expected_object_id = "456789(UNKNOWN)"
    expected_title = "Pessoa (UNKNOWN)"
    data = {"nome": name, "cpf": document}

    assert Person.base_url == EXPECTED_BASE_URL
    person = Person(data)
    assert person.entity_type == "person"
    assert person.version == 1
    assert person.name == name
    assert person.object_id == expected_object_id
    assert person.document == document
    assert person.title == expected_title


def test_Company():
    name = "BANCO DO BRASIL SA"
    legal_name = "BB AGENCIA X"
    document = "123456780001XX"
    expected_object_id = "12345678"
    expected_title = f"Empresa {name} ({legal_name})"
    data = {"cnpj": document, "razao_social": legal_name, "nome_fantasia": name}

    assert Company.base_url == EXPECTED_BASE_URL
    person = Company(data)
    assert person.entity_type == "company"
    assert person.version == 1
    assert person.name == name
    assert person.legal_name == legal_name
    assert person.object_id == expected_object_id
    assert person.document == document
    assert person.title == expected_title


def test_Company_empty_name():
    name = None
    legal_name = "BB AGENCIA X"
    document = "123456780001XX"
    expected_object_id = "12345678"
    expected_title = f"Empresa {legal_name}"
    data = {"cnpj": document, "razao_social": legal_name, "nome_fantasia": name}

    person = Company(data)
    assert person.entity_type == "company"
    assert person.version == 1
    assert person.name == name
    assert person.legal_name == legal_name
    assert person.object_id == expected_object_id
    assert person.document == document
    assert person.title == expected_title
