from copy import deepcopy

from django.db.utils import ProgrammingError
from django.test import TestCase
from model_bakery import baker

from core.models import Dataset, DataTable, Version


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
        Dataset.objects.filter(slug=cls.DATASET_SLUG).delete()
        cls.dataset = baker.make(Dataset, slug=cls.DATASET_SLUG, show=True)
        cls.version = baker.make(Version, dataset=cls.dataset)
        cls.table = baker.make(
            "core.Table",
            dataset=cls.dataset,
            name=cls.TABLE_NAME,
            version=cls.version,
            filtering=[f["name"] for f in cls.FIELDS_KWARGS if f.get("filtering")],
        )
        cls.data_table = DataTable.new_data_table(cls.table)
        cls.data_table.activate()

        for f_kwargs in [deepcopy(k) for k in cls.FIELDS_KWARGS]:
            f_kwargs.pop("filtering", None)
            f_kwargs["has_choices"] = "choices" in f_kwargs
            baker.make("core.Field", dataset=cls.dataset, table=cls.table, **f_kwargs)

        cls.TableModel = cls.table.get_model(cache=False)
        try:
            cls.TableModel.delete_table()
        except ProgrammingError:  # Does not exist
            pass
        finally:
            cls.TableModel.create_table(indexes=False)
