import io
import requests
import rows
from functools import lru_cache

from django.conf import settings
from utils.rocketchat import RocketChat


COLLABORATORS_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"


class FakeChat:

    def send_message(self, channel, message):
        print(f"New message in {channel}:\n\t{message}")


@lru_cache(maxsize=1)
def collaborators_data():
    response = requests.get(COLLABORATORS_SPREADSHEET_URL)
    url_table = rows.import_from_csv(io.BytesIO(response.content), encoding="utf-8")
    return url_table


@lru_cache(maxsize=1)
def get_chat():
    chat = FakeChat
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
    chat.send_message(channel, msg)


def notify_spreadsheet_mismatch(spreadsheet, errors):
    raise NotImplementedError
