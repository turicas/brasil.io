#!/usr/bin/env python
from urllib.parse import urljoin

import requests

#######
# INFO: esta é uma cópia de https://github.com/turicas/covid19-br/blob/master/bot/rocketchat.py


HTTP_METHODS = "GET HEAD POST PUT DELETE CONNECT OPTIONS TRACE PATCH".lower().split()


class RocketChat:
    def __init__(self, base_url):
        self.base_url = base_url

    def make_url(self, endpoint):
        return urljoin(self.base_url, f"/api/v1/{endpoint}")

    def make_request(self, method, *args, **kwargs):
        method = method.lower().strip()
        assert method in HTTP_METHODS

        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["X-Auth-Token"] = self.auth_token
        kwargs["headers"]["X-User-Id"] = self.user_id
        return getattr(requests, method)(*args, **kwargs)

    def login(self, username, password):
        self.username = username
        response = requests.post(self.make_url("login"), data={"user": username, "password": password})
        data = response.json()
        assert data["status"] == "success"
        self.user_id = data["data"]["userId"]
        self.auth_token = data["data"]["authToken"]
        self.user_data = data["data"]["me"]

    def create_bot_user(self, bot_username, bot_password, bot_email, bot_name):
        return self.make_request(
            "POST",
            self.make_url("users.create"),
            json={
                "username": bot_username,
                "password": bot_password,
                "email": bot_email,
                "name": bot_name,
                "active": True,
                "roles": ["bot"],
                "joinDefaultChannels": False,
                "requirePasswordChange": False,
                "sendWelcomeEmail": False,
                "verified": True,
            },
        )

    def send_message(self, channel, message):
        return self.make_request(
            "POST", self.make_url("chat.postMessage"), json={"channel": channel, "text": message,},
        )
