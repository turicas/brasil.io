from django.test import TestCase
from core.filters import DynamicModelFilterProcessor

class TestDynamicModelFilter(TestCase):
    def test_filter_with_all_keys_allowed(self):
        filtering = {"foo": "bar", "fu": "bá"}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, filtering)
