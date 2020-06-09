import csv
import io
import logging
import os
import socket

import requests
import requests.packages.urllib3.util.connection as urllib3_cn
import rows
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from covid19.forms import StateSpreadsheetForm
from covid19.models import StateSpreadsheet

urllib3_cn.allowed_gai_family = lambda: socket.AF_INET  # Force IPv4
STATE_TOTALS_URL = (
    "https://docs.google.com/spreadsheets/d/17mmfgPAcVCeHW3548BlFtuurAvF3jeffRVO1NW7rVgQ/export?format=csv"
)
NOTES = "Dados totais coletados da Secretaria Estadual de Saúde"
STATUS = {value: key for key, value in StateSpreadsheet.STATUS_CHOICES}
STATUS_DEPLOYED = STATUS["deployed"]


def debug(message):
    print(message)


def has_deployed_spreadsheet(state, date):
    return StateSpreadsheet.objects.filter(state=state, date=date, status=StateSpreadsheet.DEPLOYED,).exists()


class Command(BaseCommand):
    help = "Update state totals based on custom spreadsheet"

    def handle(self, *args, **kwargs):
        username = "turicas"
        debug(f"Getting user object for {username}")
        user = get_user_model().objects.get(username=username)

        debug(f"Downloading spreadsheet from {STATE_TOTALS_URL}")
        response = requests.get(STATE_TOTALS_URL)

        debug("Importing spreadsheet")
        spreadsheet = rows.import_from_csv(
            io.BytesIO(response.content),
            encoding="utf-8",
            force_types={
                "confirmed": rows.fields.IntegerField,
                "data_dados": rows.fields.DateField,
                "deaths": rows.fields.IntegerField,
            },
        )

        for row in spreadsheet:
            if str(row.origem or "").lower() != "ses":
                debug(f"Skipping {row.state} (source = {row.origem})")
                continue

            state = str(row.state or "").upper()
            date = row.data_dados
            confirmed = row.confirmed
            deaths = row.deaths

            if has_deployed_spreadsheet(state, date):
                s = StateSpreadsheet.objects.filter(state=state, date=date, status=3)
                data = [x for x in s.first().table_data if x["city"] is None][0]

                if confirmed <= data["confirmed"] or deaths <= data["deaths"]:
                    debug(f"Skipping {state} (already deployed for {date} and numbers of deployed are greater than ours: (ours vs deployed) {confirmed} vs {data['confirmed']}, {deaths} vs {data['deaths']})")
                    continue

            debug(f"Creating spreadsheet for {state} on {date}")

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
                    user=user,
                )
                form_valid = form.is_valid()
                if not form_valid:
                    debug(f"  Form is NOT valid for {state}! errors = {form.errors}")
                    continue
            os.unlink(filename)

            obj = form.save()
            obj.peer_review = obj
            obj.status = StateSpreadsheet.UPLOADED
            obj.save()
            obj.import_to_final_dataset()
            obj.refresh_from_db()
            StateSpreadsheet.objects.filter(state=state, date=date).exclude(id=obj.id).update(cancelled=True)
            debug(f"  Spreadsheet created for {state}, id = {obj.id}")
