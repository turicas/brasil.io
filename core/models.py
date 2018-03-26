from urllib.parse import urlparse

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


class Dataset(models.Model):
    author_name = models.CharField(max_length=255, null=False, blank=False)
    author_url = models.URLField(max_length=2000, null=True, blank=True)
    code_url = models.URLField(max_length=2000, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    license_name = models.CharField(max_length=255, null=False, blank=False)
    license_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    slug = models.SlugField(max_length=50, null=False, blank=False)
    source_name = models.CharField(max_length=255, null=False, blank=False)
    source_url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        return f'{self.name} (by {self.author_name}, source: {self.source_name})'


class Link(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    url = models.URLField(max_length=2000, null=False, blank=False)

    def __str__(self):
        domain = urlparse(self.url).netloc
        return f'{self.title} ({domain})'


class Version(models.Model):
    collected_at = models.DateField(null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    download_url = models.URLField(max_length=2000, null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    order = models.PositiveIntegerField(null=False, blank=False)

    def __str__(self):
        return f'{self.dataset.slug}.{self.name} (order: {self.order})'


class Table(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    default = models.BooleanField(null=False, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    options = JSONField(null=True, blank=True)
    ordering = ArrayField(models.CharField(max_length=63),
                          null=False, blank=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=False, blank=False)


    def __str__(self):
        return f'{self.dataset.slug}.{self.version.name}.{self.name}'


class Field(models.Model):
    TYPES = ['binary', 'bool', 'date', 'datetime', 'decimal', 'email',
             'float', 'integer', 'json', 'percent', 'text',]
    TYPE_CHOICES = [(value, value) for value in TYPES]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE,
                                null=False, blank=False)
    index = models.BooleanField(null=False, blank=False)
    max_length = models.PositiveSmallIntegerField(null=True, blank=True)
    name = models.CharField(max_length=63)
    options = JSONField(null=True, blank=True)
    show = models.BooleanField(null=False, blank=False)
    table = models.ForeignKey(Table, on_delete=models.CASCADE,
                              null=False, blank=False)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES,
                            null=False, blank=False)
    version = models.ForeignKey(Version, on_delete=models.CASCADE,
                                null=True, blank=True)

    def __str__(self):
        return (f'{self.dataset.slug}.{self.version.name}.{self.table.name}'
                f'.{self.name}')
