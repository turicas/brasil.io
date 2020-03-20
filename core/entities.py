import uuid
from unicodedata import normalize
from urllib.parse import urljoin


def unaccent(text):
    return normalize("NFKD", text).encode("ascii", errors="ignore").decode("ascii")


class Entity:

    base_url = None
    entity_type = None
    field_names = None
    version = None

    def __init__(self, row):
        assert self.base_url is not None
        assert self.entity_type is not None
        assert self.field_names is not None
        assert self.version is not None
        for field_name in self.field_names:
            if field_name not in row:
                raise ValueError(f"Field '{field_name}' not found")

        self.row = row

    @property
    def object_id(self):
        raise NotImplementedError()

    @property
    def title(self):
        raise NotImplementedError()

    @property
    def url(self):
        return urljoin(
            self.base_url, f"v{self.version}/{self.entity_type}/{self.object_id}"
        )

    @property
    def uuid(self):
        return uuid.uuid5(uuid.NAMESPACE_URL, self.url)

    @property
    def data(self):
        return {
            "entity_type": self.entity_type,
            "title": self.title,
            "url": self.url,
            "uuid": self.uuid,
        }


class Company(Entity):
    base_url = "https://uuid.brasil.io"
    entity_type = "company"
    field_names = ("cnpj", "nome_fantasia", "razao_social")
    version = 1

    @property
    def name(self):
        return self.row["nome_fantasia"]

    @property
    def document(self):
        return self.row["cnpj"]

    @property
    def legal_name(self):
        return self.row["razao_social"]

    @property
    def object_id(self):
        return self.row["cnpj"][:8]

    @property
    def title(self):
        if self.name:
            return f"Empresa {self.name} ({self.legal_name})"
        else:
            return f"Empresa {self.legal_name}"


class Person(Entity):
    base_url = "https://uuid.brasil.io"
    entity_type = "person"
    field_names = ("nome", "cpf")
    version = 1

    @property
    def name(self):
        return self.row["nome"]

    @property
    def document(self):
        return self.row["cpf"]

    @property
    def object_id(self):
        first_name = unaccent(self.name).split()[0].upper()
        return f"{self.document[3:9]}{first_name}"

    @property
    def title(self):
        return f"Pessoa {self.name}"
