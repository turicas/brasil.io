import csv
import io
import os
import socket

import requests
import requests.packages.urllib3.util.connection as urllib3_cn
import rows
from django.core.files.uploadedfile import SimpleUploadedFile

from covid19.forms import StateSpreadsheetForm
from covid19.models import StateSpreadsheet

urllib3_cn.allowed_gai_family = lambda: socket.AF_INET  # Force IPv4
STATE_TOTALS_URL = (
    "https://docs.google.com/spreadsheets/d/17mmfgPAcVCeHW3548BlFtuurAvF3jeffRVO1NW7rVgQ/export?format=csv"
)
NOTES = "Dados totais coletados da Secretaria Estadual de Saúde"


class UpdateStateTotalsCommand:
    def __init__(self, user, force, only):
        self.user = user
        self.force = force
        self.only = only

    def debug(self, message):
        print(message)

    def get_spreadsheet_rows(self):
        self.debug(f"Downloading spreadsheet from {STATE_TOTALS_URL}")
        # Must NOT cache this request since the spreadsheet can change a lot
        # during the bulletin process.
        response = requests.get(STATE_TOTALS_URL)

        self.debug("Importing spreadsheet")
        return rows.import_from_csv(
            io.BytesIO(response.content),
            encoding="utf-8",
            force_types={
                "confirmed": rows.fields.IntegerField,
                "data_dados": rows.fields.DateField,
                "deaths": rows.fields.IntegerField,
            },
        )

    def process_state_row(self, row):
        state = str(row.state or "").upper()
        if self.only and state not in self.only:
            self.debug(f"{state} - SKIPPING - It's not in --only")
            return

        date = row.data_dados
        confirmed = row.confirmed
        deaths = row.deaths

        recent_deploy = StateSpreadsheet.objects.most_recent_deployed(state, date)
        message = None
        status = str(row.status or "").strip().lower()
        if status != "ok":
            self.debug(f"{state} - SKIPPING - status = {status}")
            return

        elif recent_deploy:
            data = recent_deploy.get_total_data()

            if confirmed == data["confirmed"] and deaths == data["deaths"]:
                self.debug(f"{state} - SKIPPING - Has the same total for deaths and confirmed")
                return
            elif confirmed < data["confirmed"] or deaths < data["deaths"]:
                if self.force and state in self.force:
                    message = f"{state} - WARNING - Would skip (already deployed for {date} and numbers of deployed are greater than ours: (ours vs deployed) {confirmed} vs {data['confirmed']}, {deaths} vs {data['deaths']}), but updating because of --force"
                else:
                    self.debug(
                        f"{state} - SKIPPING - Already deployed for {date} and numbers of deployed are greater than ours: (ours vs deployed) {confirmed} vs {data['confirmed']}, {deaths} vs {data['deaths']}"
                    )
                    return
            else:
                message = f"{state} - CREATING - date: {date}"

        else:
            message = f"{state} - CREATING - date: {date}"

        filename = f"/tmp/{state}-{date}.csv"
        with open(filename, mode="w") as fobj:
            writer = csv.writer(fobj)
            writer.writerow(["municipio", "confirmados", "obitos"])
            writer.writerow(["TOTAL NO ESTADO", str(confirmed), str(deaths)])

        with open(filename, mode="rb") as fobj:
            file_data = fobj.read()
            form = StateSpreadsheetForm(
                {"date": date, "state": state, "boletim_urls": STATE_TOTALS_URL, "boletim_notes": NOTES,},
                {"file": SimpleUploadedFile(filename, file_data),},
                user=self.user,
            )
            form_valid = form.is_valid()
            if not form_valid:
                self.debug(f"{state} - ERROR CREATING - Invalid form: {form.errors}")
                return
        os.unlink(filename)

        obj = form.save()
        StateSpreadsheet.objects.cancel_older_versions(obj)
        obj.link_to(obj)
        obj.import_to_final_dataset()
        obj.refresh_from_db()
        message += f", id = {obj.id}"
        self.debug(message)

    @classmethod
    def execute(cls, user, force=None, only=None):
        self = cls(user, force or [], only or [])
        for row in self.get_spreadsheet_rows():
            self.process_state_row(row)
