from django.test import TestCase
from core.filters import DynamicModelFilterProcessor

class TestDynamicModelFilter(TestCase):
    def test_filter_with_all_keys_allowed(self):
        filtering = {"foo": "bar", "fu": "bá"}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, filtering)

    def test_remove_filter_not_allowed(self):
        filtering = {"foo": "bar", "fu": "bá"}
        allowed_filters = ["foo"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, {"foo": "bar"})


    def test_remove_None_filter(self):
        filtering = {"foo": "bar", "fu": None}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, {"foo": "bar"})

    def test_clean_bool_lowercase_values(self):
        filtering = {"foo": "true", "fu": "false"}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, {"foo": True, "fu": False})

    def test_accept_empty_string(self):
        filtering = {"foo": "bar", "fu": "bá", "zen": ""}
        allowed_filters = ["foo", "fu", "zen"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEquals(filter_processor.filters, {"foo": "bar", "fu": "bá", "zen": ""})
