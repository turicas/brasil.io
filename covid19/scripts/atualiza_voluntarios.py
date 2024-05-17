import io
import json

import rows

from project.storage import storage


def make_row(row, active):
    return {
        "name": row.name,
        "personal_url": row.personal_url,
        "avatar_url": f"https://data.brasil.io/mirror/covid19/voluntarios/{row.username_chat}.jpeg",
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

    temp = io.BytesIO()
    json.dump(volunteers, temp)
    temp.seek(0)
    storage.upload_file(
        fobj=temp,
        bucket="meta",
        filename="covid19-voluntarios.json",
        content_type="application/json",
    )
