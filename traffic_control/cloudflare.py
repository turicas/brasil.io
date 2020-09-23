import os
from urllib.parse import urljoin

import requests


class Cloudflare:
    base_url = "https://api.cloudflare.com/client/v4/"

    def __init__(self, email, key):
        self.__auth_email = email
        self.__auth_key = key
        self.__auth_headers = {
            "X-AUTH-KEY": key,
            "X-AUTH-EMAIL": email,
        }

    def get_http_headers(self):
        headers = self.__auth_headers.copy()
        headers["Content-Type"] = "application/json"
        return headers

    def request(self, path, query_string=None, data=None, headers=None, method="get"):
        request_headers = self.get_http_headers()
        if headers is not None:
            request_headers.update(headers)

        http_request_func = getattr(requests, method.lower())
        url = urljoin(self.base_url, path)
        response = http_request_func(url, params=query_string, headers=request_headers, data=data)
        data = response.json()
        if not data.get("success", False):
            raise ValueError(f"Error on respose: {data}")
        return data

    def paginate(self, path, query_string=None, data=None, headers=None, method="get"):
        query_string = query_string or {}
        finished, page = False, 1
        while not finished:
            query_string["page"] = page
            response = self.request(path, query_string=query_string, data=data, headers=headers, method=method)
            for result in response["result"]:
                yield result
            if "result_info" not in response:
                finished = True
            else:
                pagination_info = response["result_info"]
                if "page" in pagination_info:
                    finished = pagination_info["page"] == pagination_info["total_pages"]
                elif "cursors" in pagination_info:
                    # TODO: implement (required for listing list items)
                    raise NotImplementedError("cursor-based pagination was not implemented")
                else:
                    raise RuntimeError("Received unrecognized pagination information")

    def accounts(self):
        yield from self.paginate("accounts")

    def rules_list(self, account_id):
        yield from self.paginate(f"accounts/{account_id}/rules/lists")


if __name__ == "__main__":
    key = os.environ["CLOUDFLARE_AUTH_KEY"]
    email = os.environ["CLOUDFLARE_AUTH_EMAIL"]
    desired_account_name = "Pythonic Café"
    desired_list_name = "blocked_ips"

    cf = Cloudflare(email, key)

    # Get account ID
    account_id = None
    for obj in cf.accounts():
        if obj["name"] == desired_account_name:
            account_id = obj["id"]
            break

    # Get list ID
    list_id = None
    for obj in cf.rules_list(account_id):
        if obj["name"] == desired_list_name:
            list_id = obj["id"]
            break
