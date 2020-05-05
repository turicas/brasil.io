from functools import lru_cache

from django.conf import settings

from covid19.google_data import import_info_by_state
from utils.rocketchat import RocketChat


class FakeChat:
    def send_message(self, channel, message):
        print(f"New message in {channel}:\n{message}")


@lru_cache(maxsize=1)
def get_chat():
    chat = FakeChat()
    if settings.ROCKETCHAT_BASE_URL:
        chat = RocketChat(settings.ROCKETCHAT_BASE_URL)
        chat.user_id = settings.ROCKETCHAT_USER_ID
        chat.auth_token = settings.ROCKETCHAT_AUTH_TOKEN
    return chat


def clean_collaborators(collaborators):
    return ["@" + c.strip() for c in collaborators.split(",")]


def notification_info_by_state(state):
    state_info = import_info_by_state(state)
    channel = state_info.canal
    collabs = clean_collaborators(state_info.voluntarios)
    collabs = " ".join(collabs)
    return channel, collabs


def notify_new_spreadsheet(spreadsheet):
    chat = get_chat()
    channel, collabs = notification_info_by_state(spreadsheet.state)

    msg = f"{collabs} - *Nova planilha* importada para o estado *{spreadsheet.state}* para o dia *{spreadsheet.date}*"
    msg += f"\nRealizada por: @{spreadsheet.user.username}\n\nPrecisamos de mais uma planilha para verificar os dados."  # noqa
    msg += "\nOs dados só poderão ser atualizados se uma nova planilha for enviada e os dados forem os mesmos."

    chat.send_message(channel, msg)


def notify_spreadsheet_mismatch(spreadsheet, errors):
    chat = get_chat()
    channel, collabs = notification_info_by_state(spreadsheet.state)

    errors = "\n- ".join(errors)
    msg = f"{collabs} - *Dados divergentes* na planilha importada para o estado *{spreadsheet.state}* para o dia *{spreadsheet.date}*"  # noqa
    msg += f"\nRealizada por: @{spreadsheet.user.username}\n\n- {errors}"
    msg += f"\n\nLink para a planilha: https://brasil.io{spreadsheet.admin_url}"

    chat.send_message(channel, msg)


def notify_import_success(spreadsheet):
    chat = get_chat()
    channel = "#covid19"
    authors = " e ".join([f"@{spreadsheet.user.username}", f"@{spreadsheet.peer_review.user.username}",])

    msg = f"@turicas planilha de *{spreadsheet.state}* para o dia *{spreadsheet.date}* checada (dados enviados por {authors}), pode rodar o deploy!"  # noqa
    msg += f"\nLink para a planilha: https://brasil.io{spreadsheet.admin_url}"
    chat.send_message(channel, msg)

    channel, collabs = notification_info_by_state(spreadsheet.state)

    msg = f"{collabs} - planilha de *{spreadsheet.state}* para o dia *{spreadsheet.date}* checada pronta para o deploy!"  # noqa
    msg += f"\nDados enviados por {authors}"
    msg += f"\nLink para a planilha: https://brasil.io{spreadsheet.admin_url}"
    chat.send_message(channel, msg)
