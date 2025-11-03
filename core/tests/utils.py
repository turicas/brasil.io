from copy import deepcopy

from django.apps.registry import apps
from django.db.utils import ProgrammingError
from django.test import TestCase
from model_bakery import baker

from core.models import Dataset, DataTable, Field, Table, Version


def create_model(dataset_slug, table_name, fields_kwargs):
    Dataset.objects.filter(slug=dataset_slug).delete()
    dataset = baker.make(Dataset, slug=dataset_slug, show=True)
    version = baker.make(Version, dataset=dataset)
    table = baker.make(
        Table,
        dataset=dataset,
        hidden=False,
        name=table_name,
        version=version,
        ordering=["-id"],
    )
    data_table = DataTable.new_data_table(table)
    data_table.activate()
    for f_kwargs in [deepcopy(k) for k in fields_kwargs]:
        f_kwargs["frontend_filter"] = bool(f_kwargs.pop("filtering", None))
        f_kwargs["has_choices"] = "choices" in f_kwargs
        baker.make(Field, dataset=dataset, table=table, **f_kwargs)
    return dataset, version, table


def setup_model(table, cache=False):
    Model = table.get_model(cache=cache)
    try:
        Model.delete_table()
    except ProgrammingError:  # Does not exist
        pass
    finally:
        Model.create_table(indexes=False)
    return Model


def unregister_model(Model):
    model_name_lower = Model._meta.model_name.lower()
    if model_name_lower in apps.all_models["core"]:
        del apps.all_models["core"][model_name_lower]


class BaseTestCaseWithSampleDataset(TestCase):
    """
    Base test case class to prepare Brasil.io's DB to have a sample dataset.

    Must define the class attributes DATASET_SLUG, TABLE_NAME and FIELDS_KWARGS to inherit and use it
    """

    DATASET_SLUG = ""
    TABLE_NAME = ""
    FIELDS_KWARGS = []

    @classmethod
    def validate_config(cls):
        required_attrs = ["DATASET_SLUG", "TABLE_NAME", "FIELDS_KWARGS"]
        name = cls.__name__

        for attr in required_attrs:
            if not getattr(cls, attr, None):
                raise ValueError(f"{name}.{attr} cannot be empty")

        is_iterable = issubclass(type(cls.FIELDS_KWARGS), (list, tuple, set))
        if not (is_iterable and all(type(kw) is dict for kw in cls.FIELDS_KWARGS)):
            raise ValueError(
                f"{name}.FIELDS_KWARGS must be an iterable with model fields' description dicts, not {type(cls.FIELDS_KWARGS).__name__}"
            )

    @classmethod
    def setUpTestData(cls):
        cls.validate_config()
        cls.dataset, cls.version, cls.table = create_model(cls.DATASET_SLUG, cls.TABLE_NAME, cls.FIELDS_KWARGS)
        cls.TableModel = setup_model(cls.table)

    @classmethod
    def tearDownClass(cls):
        unregister_model(cls.TableModel)
        super().tearDownClass()
