import json
import os
import tempfile

import rows

from core.util import upload_file


def make_row(row, active):
    return {
        "name": row.name,
        "personal_url": row.personal_url,
        "avatar_url": f"https://chat.brasil.io/avatar/{row.username_chat}",
        "active": active,
    }


def run(*args, **kwargs):
    # Read needed argument - input filename
    # TODO: change to gspread and authenticate with brasilio credentials
    if not args:
        print("ERROR - Missing: --script-args <input_filename>")
        exit(1)
    input_filename = args[0]

    # Read file contents
    active = rows.import_from_xlsx(input_filename, sheet_name="Contatos")
    inactive = rows.import_from_xlsx(input_filename, sheet_name="ex-voluntarios")

    # Convert to final format
    volunteers = [make_row(row, active=True) for row in active if row.username_chat] + [
        make_row(row, active=False) for row in inactive if row.username_chat
    ]

    # Save into temp JSON file
    temp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    temp.file.write(json.dumps(volunteers))
    temp.file.close()

    # Upload file to storage system used by backend
    upload_file(
        temp.name, bucket="meta", remote_filename="covid19-voluntarios.json", progress=True,
    )

    # Delete temp file
    os.unlink(temp.name)
