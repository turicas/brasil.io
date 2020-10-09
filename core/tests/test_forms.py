from django.forms import ChoiceField

from core.forms import get_table_dynamic_form
from core.tests.utils import BaseTestCaseWithSampleDataset


class DynamicModelFormTests(BaseTestCaseWithSampleDataset):
    DATASET_SLUG = "sample"
    TABLE_NAME = "sample_table"
    FIELDS_KWARGS = [
        {"name": "name", "options": {"max_length": 50}, "type": "text", "null": False},
        {"name": "uf", "options": {"max_length": 2}, "type": "text", "null": False},
        {"name": "city", "options": {"max_length": 50}, "type": "text", "null": False},
    ]

    def setUp(self):
        self.table.field_set.all().update(frontend_filter=False)
        self.table.save()

    def get_model_field(self, name):
        return [f for f in self.TableModel._meta.fields if f.name == name][0]

    def test_table_without_filters_gets_empty_form(self):
        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss()
        assert 0 == len(form.fields)

    def test_generate_form_based_in_table_filtering(self):
        self.table.field_set.filter(name__in=["uf", "city"]).update(frontend_filter=True)

        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss()

        assert "uf" in form.fields
        assert "city" in form.fields
        assert isinstance(form.fields["uf"], type(self.get_model_field("uf").formfield()))
        assert isinstance(form.fields["city"], type(self.get_model_field("city").formfield()))

    def test_filter_form_does_not_invalidate_if_no_data(self):
        self.table.field_set.filter(name__in=["uf", "city"]).update(frontend_filter=True)

        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss(data={})

        assert form.is_valid()
        assert {"uf": "", "city": ""} == form.cleaned_data

    def test_validate_form_against_field_choices(self):
        self.table.field_set.filter(name__in=["uf", "city"]).update(frontend_filter=True)
        uf_field = self.table.get_field("uf")
        uf_field.has_choices = True
        uf_field.choices = {"data": ["RJ", "SP", "MG"]}
        uf_field.save()
        city_field = self.table.get_field("city")
        city_field.has_choices = True
        city_field.choices = {"data": ["Rio de Janeiro", "São Pauyo", "Belo Horizonte"]}
        city_field.save()

        # valid form
        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss(data={"uf": "RJ", "city": "Rio de Janeiro"})
        assert isinstance(form.fields["uf"], ChoiceField)
        assert isinstance(form.fields["city"], ChoiceField)
        assert form.is_valid()
        assert {"uf": "RJ", "city": "Rio de Janeiro"} == form.cleaned_data

        # invalid form
        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss(data={"uf": "XXX", "city": "Rio de Janeiro"})
        assert not form.is_valid()
        assert "uf" in form.errors
        assert "city" not in form.errors
        assert {"city": "Rio de Janeiro"} == form.cleaned_data

    def test_choice_failback_to_default_type_if_has_choice_field_but_no_data(self):
        self.table.field_set.filter(name__in=["uf", "city"]).update(frontend_filter=True)
        uf_field = self.table.get_field("uf")
        uf_field.has_choices = True
        uf_field.save()
        city_field = self.table.get_field("city")
        city_field.has_choices = True
        city_field.save()

        DynamicFormClasss = get_table_dynamic_form(self.table, cache=False)
        form = DynamicFormClasss()

        assert "uf" in form.fields
        assert "city" in form.fields
        assert isinstance(form.fields["uf"], type(self.get_model_field("uf").formfield()))
        assert isinstance(form.fields["city"], type(self.get_model_field("city").formfield()))
