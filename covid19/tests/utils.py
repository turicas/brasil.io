from model_bakery import baker

from django.db.utils import ProgrammingError
from django.test import TestCase

from core.models import Dataset, Table


class Covid19DatasetTestCase(TestCase):
    """
    Base test case class to prepare Brasil.io's DB to have Covid-19 cases dataset.

    In the future, this can be refactored to a generic purpose TestCase class so the tests can
    configure the dataset, table and fields they'll interact with.
    """
    DATASET_SLUG = 'covid19'
    CASES_TABLE_NAME = 'caso'
    FIELDS_KWARGS = [
        {'name': 'date', 'options': {'max_length': 10}, "type": "text", "null": False},
        {'name': 'state', 'options': {'max_length': 2}, "type": "string", "null": False},
        {'name': 'city', 'options': {'max_length': 64}, "type": "string", "null": True},
        {'name': 'place_type', 'options': {'max_length': 5}, "type": "string", "null": False},
        {'name': 'confirmed', 'options': {}, "type": "integer", "null": False},
        {'name': 'deaths', 'options': {}, "type": "integer", "null": True},
        {'name': 'is_last', 'options': {}, "type": "bool", "null": False},
        {'name': 'estimated_population_2019', 'options': {}, "type": "integer", "null": True},
        {'name': 'city_ibge_code', 'options': {'max_length': 127}, "type": "string", "null": True},
        {'name': 'confirmed_per_100k_inhabitants', 'options': {}, "type": "float", "null": True},
        {'name': 'death_rate', 'options': {}, "type": "float", "null": True},
        {'name': 'order_for_place', 'options': {}, "type": "integer", "null": False},
    ]

    @classmethod
    def setUpTestData(cls):
        Dataset.objects.filter(slug=cls.DATASET_SLUG).delete()
        cls.covid19 = baker.make(Dataset, slug=cls.DATASET_SLUG)
        cls.cases_table = baker.make(Table, dataset=cls.covid19, name=cls.CASES_TABLE_NAME)

        for f_kwargs in cls.FIELDS_KWARGS:
            baker.make('core.Field', dataset=cls.covid19, table=cls.cases_table, **f_kwargs)

        cls.Covid19Cases = cls.cases_table.get_model(cache=False)
        try:
            cls.Covid19Cases.delete_table()
        except ProgrammingError:  # Does not exist
            pass
        finally:
            cls.Covid19Cases.create_table(create_indexes=False)
