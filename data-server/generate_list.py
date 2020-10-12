import argparse
import hashlib
import os
from pathlib import Path

from jinja2 import Template
from tqdm import tqdm


def sha512sum(filename, buffer_size=1 * 1024 * 1024):
    obj = hashlib.sha512()
    with open(filename, mode="rb") as fobj:
        finished = False
        while not finished:
            data = fobj.read(buffer_size)
            finished = len(data) == 0
            if not finished:
                obj.update(data)
    return obj.hexdigest()


def human_readable_size(size, divider=1024):
    """
    >>> human_readable_size(100)
    '100B'
    >>> human_readable_size(1023)
    '1023B'
    >>> human_readable_size(1024)
    '1kB'
    >>> human_readable_size(1.5 * 1024)
    '1.50kB'
    >>> human_readable_size(1024 * 1024)
    '1MB'
    >>> human_readable_size(1024 * 1024 * 1024)
    '1GB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024)
    '1TB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024)
    '1PB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024 * 1024)
    '1EB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024)
    '1024EB'
    """

    multipliers = list("kMGTPE")
    multiplier = ""
    while size >= divider and multipliers:
        size /= divider
        multiplier = multipliers.pop(0)
    if size - int(size) > 0:
        return f"{size:4.2f}{multiplier}B".strip()
    else:
        return f"{int(size):4}{multiplier}B".strip()


def make_file_row(relative_path, full_path):
    file_size = os.path.getsize(full_path)
    return {
        "filename": relative_path,
        "sha512sum": sha512sum(full_path),
        "size": human_readable_size(file_size),
    }


def render_template(template_filename, context):
    with open(template_filename) as fobj:
        template = Template(fobj.read())
    return template.render(**context)


if __name__ == "__main__":
    TEMPLATE_PATH = Path(__file__).parent / "templates"
    list_template = TEMPLATE_PATH / "list.html"

    parser = argparse.ArgumentParser()
    parser.add_argument("list_type", choices=["mirror", "dataset"])
    parser.add_argument("dataset")
    parser.add_argument("capture_date")
    parser.add_argument("files_path")
    args = parser.parse_args()
    files_path = Path(args.files_path)

    file_list = []
    progress = tqdm()
    for root, dirs, filenames in os.walk(files_path):
        for filename in filenames:
            full_path = Path(root) / filename
            relative_path = str(full_path.relative_to(files_path))
            if relative_path in ("_meta/list.html", "SHA512SUMS"):
                continue
            file_list.append(make_file_row(relative_path, full_path))
            progress.update()

    file_list.sort(key=lambda row: row["filename"])
    with open(files_path / "SHA512SUMS", "w") as fobj:
        for f in file_list:
            fobj.write(f"{f['sha512sum']}  {f['filename']}\n")
    file_list.append(make_file_row("SHA512SUMS", files_path / "SHA512SUMS"))

    context = {
        "list_type": args.list_type,
        "file_list": file_list,
        "dataset": args.dataset,
        "capture_date": args.capture_date,
    }
    list_filename = files_path / "_meta" / "list.html"
    if not list_filename.parent.exists():
        list_filename.parent.mkdir()
    with open(list_filename, mode="w") as fobj:
        fobj.write(render_template(list_template, context))
