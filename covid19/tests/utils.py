from core.tests.utils import BaseTestCaseWithSampleDataset


class Covid19DatasetTestCase(BaseTestCaseWithSampleDataset):
    """
    Base test case class to prepare Brasil.io's DB to have Covid-19 cases dataset.
    """

    DATASET_SLUG = "covid19"
    TABLE_NAME = "caso"
    FIELDS_KWARGS = [
        {"name": "date", "options": {"max_length": 10}, "type": "text", "null": False},
        {"name": "state", "options": {"max_length": 2}, "type": "string", "null": False},
        {"name": "city", "options": {"max_length": 64}, "type": "string", "null": True},
        {"name": "place_type", "options": {"max_length": 5}, "type": "string", "null": False},
        {"name": "confirmed", "options": {}, "type": "integer", "null": False},
        {"name": "deaths", "options": {}, "type": "integer", "null": True},
        {"name": "is_last", "options": {}, "type": "bool", "null": False},
        {"name": "estimated_population_2019", "options": {}, "type": "integer", "null": True},
        {"name": "estimated_population", "options": {}, "type": "integer", "null": True},
        {"name": "city_ibge_code", "options": {"max_length": 127}, "type": "string", "null": True},
        {"name": "confirmed_per_100k_inhabitants", "options": {}, "type": "float", "null": True},
        {"name": "death_rate", "options": {}, "type": "float", "null": True},
        {"name": "order_for_place", "options": {}, "type": "integer", "null": False},
    ]
