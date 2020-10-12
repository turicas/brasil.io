#!/usr/bin/env python3
import argparse
import csv
import datetime
from collections import OrderedDict, defaultdict
from itertools import islice
from pathlib import Path
from textwrap import dedent

from rows import Table, export_to_xls, fields
from rows.utils import open_compressed
from tqdm import tqdm

MAX_COLUMN_SIZE = 16 * (1024 ** 2)  # 16 MiB
csv.field_size_limit(MAX_COLUMN_SIZE)


class BrasilIOTypeDetector(fields.TypeDetector):
    """Type detector which remembers min/max sizes and create choices"""

    def __init__(self, field_names, max_choices=100, *args, **kwargs):
        super().__init__(field_names, *args, **kwargs)
        self.min_sizes = defaultdict(lambda: MAX_COLUMN_SIZE)
        self.max_sizes = defaultdict(lambda: 0)
        self.max_choices = max_choices
        self.choices = defaultdict(set)

    def process_row(self, row):
        for index, value in enumerate(row):
            if index in self._skip:
                continue
            self.check_type(index, value)

            value_length = len(fields.as_string(value))
            self.min_sizes[index] = min(self.min_sizes[index], value_length)
            self.max_sizes[index] = max(self.max_sizes[index], value_length)

            if self.choices[index] is not None:
                if len(self.choices[index]) > self.max_choices:
                    self.choices[index] = None
                else:
                    self.choices[index].add(value)


def make_title(field_name):
    """
    >>> make_title("uf")
    'UF'
    >>> make_title("nome do cidadao")
    'Nome do Cidadão'
    >>> make_title("data_da_eleicao")
    'Data da Eleição'
    """

    title = field_name.replace("_", " ").title()
    new_title = []
    for word in title.split():
        if word.lower() in ("uf", "cpf", "cnpj", "id"):
            word = word.upper()
        elif word.lower() in ("da", "das", "de", "do", "dos"):
            word = word.lower()
        elif word.endswith("cao"):
            word = word[:-3] + "ção"
        elif word.endswith("ao"):
            word = word[:-2] + "ão"
        new_title.append(word)

    return " ".join(new_title)


def detect_schema(dataset_slug, tablename, version_name, filename, encoding, samples):

    # TODO: max_length should not be filled if field type is `date`
    # TODO: should be able to force some fields (example: CPF as string)

    if samples:
        total = samples
    else:
        desc = "Counting number of rows"
        reader = csv.reader(open_compressed(filename))
        _ = next(reader)  # Skip header
        total = sum(1 for line in tqdm(reader, desc=desc, unit=" rows"))

    desc = "Creating schema using {}".format(f"{samples} samples" if samples else "all rows")
    reader = csv.reader(open_compressed(filename))
    header = next(reader)
    iterator = tqdm(reader, desc=desc, total=total)
    if samples:
        iterator = islice(iterator, samples)

    detector = BrasilIOTypeDetector(header)
    detector.feed(iterator)

    result = Table(
        fields=OrderedDict(
            [
                ("dataset_slug", fields.TextField),
                ("table_name", fields.TextField),
                ("version_name", fields.TextField),
                ("order", fields.IntegerField),
                ("obfuscate", fields.BoolField),
                ("name", fields.TextField),
                ("title", fields.TextField),
                ("description", fields.TextField),
                ("type", fields.TextField),
                ("null", fields.BoolField),
                ("has_choices", fields.BoolField),
                ("options", fields.JSONField),
                ("show", fields.BoolField),
                ("show_on_frontend", fields.BoolField),
                ("frontend_filter", fields.BoolField),
                ("link_template", fields.TextField),
                ("searchable", fields.BoolField),
            ]
        )
    )

    for index, (field_name, field_type) in enumerate(detector.fields.items()):
        # TODO: replace "string" with "text" inside Brasil.IO's code
        field_type = (
            field_type.__name__.lower().replace("field", "").replace("text", "string").replace("float", "decimal")
        )
        title = make_title(field_name)
        min_size, max_size = detector.min_sizes[index], detector.max_sizes[index]
        options = {"max_length": max_size}
        if field_type == "decimal":
            options["max_digits"] = options.pop("max_length")
            options["decimal_places"] = 2
        has_choices = detector.choices[index] is not None
        link_template = ""
        if "cnpj" in field_name or "cpf" in field_name:
            link_template = "/especiais/documento/{{ " + field_name + "|encrypt_if_needed }}"

        result.append(
            {
                "dataset_slug": dataset_slug,
                "description": title,
                "frontend_filter": has_choices,
                "has_choices": has_choices,
                "link_template": link_template,
                "order": index + 1,
                "null": min_size == 0,
                "name": field_name,
                "options": options,
                "obfuscate": bool(link_template),
                "show": True,
                "show_on_frontend": True,
                "table_name": table_name,
                "title": title,
                "type": field_type,
                "version_name": version_name,
                "searchable": field_type in ("string", "text"),
            }
        )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=dedent(
            """
    Detects schema based on data (must be CSV, could be compressed using gz, xz
    or bz2). Outputs a spreadsheet expected by Brasil.IO's `update_data`
    management command.

    The filename path is important to define the dataset_slug and table_name
    fields (should end with `dataset_slug/table_name.csv[.gz|.xz|.bz2]`, like
    in:

        python scripts/detect_schema.py data/mydataset/mytable.csv.gz
    """
        ).strip()
    )
    parser.add_argument("filename")
    parser.add_argument("--encoding", default="utf-8")
    parser.add_argument("--samples", default=30000, type=int)
    parser.add_argument("--output_path", default="schema")
    args = parser.parse_args()
    filename = Path(args.filename)

    dataset_slug = filename.parent.name
    table_name = filename.name.split(".")[0]
    today = datetime.datetime.now()
    version_name = "{}-{:02d}".format(today.year, today.month)
    result = detect_schema(dataset_slug, table_name, version_name, filename, args.encoding, args.samples)

    output_path = Path(args.output_path)
    if not output_path.exists():
        output_path.mkdir()
    output = output_path / f"schema_{dataset_slug}_{table_name}.xls"
    print(f"Writing schema to {output}...", end="")
    export_to_xls(result, output)
    print(" done!")
