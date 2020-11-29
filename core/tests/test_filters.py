from django.test import TestCase

from core.filters import DynamicModelFilterProcessor, parse_querystring


class TestDynamicModelFilter(TestCase):
    def test_filter_with_all_keys_allowed(self):
        filtering = {"foo": "bar", "fu": "bá"}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        self.assertEqual(filter_processor.filters, filtering)

    def test_remove_filter_not_allowed(self):
        filtering = {"foo": "bar", "fu": "bá"}
        allowed_filters = ["foo"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        expected = {"foo": "bar"}
        self.assertEqual(filter_processor.filters, expected)

    def test_remove_None_filter(self):
        filtering = {"foo": "bar", "fu": None}
        allowed_filters = ["foo", "fu"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        expected = {"foo": "bar"}
        self.assertEqual(filter_processor.filters, expected)

    def test_clean_string_None_to_isnull(self):
        filtering = {"foo": "bar", "fu": "bá", "none": "None"}
        allowed_filters = ["foo", "fu", "none"]

        filter_processor = DynamicModelFilterProcessor(filtering, allowed_filters)

        expected = {"foo": "bar", "fu": "bá", "none__isnull": True}
        self.assertEqual(filter_processor.filters, expected)

    def test_parse_querystring_values(self):
        querystring = {"foo": "true", "fu": "false", "bar": "t", "lorem": "F"}
        query = parse_querystring(querystring)[0]
        expected = {"foo": True, "fu": False, "bar": True, "lorem": False}
        self.assertEqual(query, expected)
