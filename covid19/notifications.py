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


@lru_cache(maxsize=1):
def get_chat():
    chat = FakeChat
    if settings.ROCKETCHAT_BASE_URL:
        chat = RocketChat(settings.ROCKETCHAT_BASE_URL)
        chat.user_id = settings.ROCKETCHAT_USER_ID
        chat.auth_token = settings.ROCKETCHAT_AUTH_TOKEN
    return chat


def get_state_row(state):
    data = collaborators_data()
    return [r for r in data if r.uf.upper() == state.upper()][0]


def notify_new_spreadsheet(spreadsheet):
    raise NotImplementedError


def notify_spreadsheet_mismatch(spreadsheet, errors):
    raise NotImplementedError
