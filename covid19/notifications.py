import io
import requests
import rows
from functools import lru_cache

from django.conf import settings
from utils.rocketchat import RocketChat


COLLABORATORS_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"


class FakeChat:

    def send_message(self, channel, message):
        print(f"New message in {channel}:\n{message}")


@lru_cache(maxsize=1)
def collaborators_data():
    response = requests.get(COLLABORATORS_SPREADSHEET_URL)
    url_table = rows.import_from_csv(io.BytesIO(response.content), encoding="utf-8")
    return url_table


@lru_cache(maxsize=1)
def get_chat():
    chat = FakeChat()
    if settings.ROCKETCHAT_BASE_URL:
        chat = RocketChat(settings.ROCKETCHAT_BASE_URL)
        chat.user_id = settings.ROCKETCHAT_USER_ID
        chat.auth_token = settings.ROCKETCHAT_AUTH_TOKEN
    return chat


def import_info_by_state(state):
    data = collaborators_data()
    return [r for r in data if r.uf.upper() == state.upper()][0]


def clean_collaborators(collaborators):
    return ['@' + c.strip() for c in collaborators.split(',')]


def notify_new_spreadsheet(spreadsheet):
    chat = get_chat()
    state_info = import_info_by_state(spreadsheet.state)
    channel = state_info.canal
    collabs = clean_collaborators(state_info.voluntarios)
    collabs = ' '.join(collabs)

    msg = f"{collabs} - *Nova planilha* importada para o estado *{spreadsheet.state}* para o dia *{spreadsheet.date}*"
    msg += f"\nRealizada por: *{spreadsheet.user.username}*\n\nPrecisamos de mais uma planilha para verificar os dados."
    msg += "\nOs dados só poderão ser atualizados se uma nova planilha for enviada e os dados serem os mesmos."

    chat.send_message(channel, msg)


def notify_spreadsheet_mismatch(spreadsheet, errors):
    chat = get_chat()
    state_info = import_info_by_state(spreadsheet.state)
    channel = state_info.canal
    collabs = clean_collaborators(state_info.voluntarios)
    collabs = ' '.join(collabs)

    errors = "\n- ".join(errors)
    msg = f"{collabs} - *Dados divergentes* na planilha importada para o estado *{spreadsheet.state}* para o dia *{spreadsheet.date}*"
    msg += f"\nRealizada por: *{spreadsheet.user.username}*\n\n- {errors}"

    chat.send_message(channel, msg)


def notify_import_success(spreadsheet):
    chat = get_chat()
    state_info = import_info_by_state(spreadsheet.state)
    channel = "#covid19"
    collabs = clean_collaborators(state_info.voluntarios)
    collabs = ' '.join(collabs)
    authors = ' e '.join([
        spreadsheet.user.username,
        spreadsheet.peer_review.user.username,
    ])

    msg = f"@turicas planilha de {spreadsheet.state} para o dia {spreadsheet.date} checada (dados enviados por {authors}), pode rodar o deploy!"

    chat.send_message(channel, msg)
