import time

from django.core.management.base import BaseCommand

from core.models import Dataset


class Command(BaseCommand):
    help = 'Update choices cache'

    def handle(self, *args, **kwargs):
        for dataset in Dataset.objects.all().iterator():
            print('{}...'.format(dataset.slug))
            start_dataset = time.time()
            Model = dataset.get_last_data_model()
            # TODO: change when add table support
            choiceables = dataset.field_set.filter(show_on_frontend=True,
                                                   has_choices=True)
            for field in choiceables:
                start = time.time()
                print('  {}... '.format(field.name), end='', flush=True)
                choices = Model.objects.order_by(field.name)\
                                       .distinct(field.name)\
                                       .values_list(field.name, flat=True)
                field.choices = {'data': [str(value) for value in choices]}
                field.save()
                end = time.time()
                print('done in {:7.3f}s.'.format(end - start))
            end_dataset = time.time()
            print('  dataset done in: {:7.3f}s.'.format(end_dataset - start_dataset))
