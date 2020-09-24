import json
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
        method = method.lower()
        if headers is not None:
            request_headers.update(headers)
        if method in ["post", "put", "delete"] and data:
            data = json.dumps(data)

        http_request_func = getattr(requests, method)
        url = urljoin(self.base_url, path)
        response = http_request_func(url, params=query_string, headers=request_headers, data=data)
        data = response.json()
        if not data.get("success", False):
            raise ValueError(f"Error on respose: {data}")
        return data

    def paginate(self, path, query_string=None, data=None, headers=None, method="get", result_class=dict):
        query_string = query_string or {}
        finished, page, cursor = False, 1, None
        while not finished:
            if page is not None:
                query_string["page"] = page
            else:
                if "page" in query_string:
                    del query_string["page"]
                query_string["cursor"] = cursor
            response = self.request(path, query_string=query_string, data=data, headers=headers, method=method)
            for result in response["result"]:
                yield result_class(result)

            pagination_info = response.get("result_info", None)
            if pagination_info is None:  # No pagination
                finished = True
                continue
            if "page" in pagination_info:
                page += 1
                finished = pagination_info["page"] == pagination_info["total_pages"]
            elif "cursors" in pagination_info:
                page = None
                if "after" in pagination_info["cursors"]:
                    cursor = pagination_info["cursors"]["after"]
                else:
                    finished = True
            else:
                raise RuntimeError("Received unrecognized pagination information")

    def accounts(self):
        yield from self.paginate("accounts")

    def rules_list(self, account_id):
        yield from self.paginate(f"accounts/{account_id}/rules/lists")

    def rules_list_items(self, account_id, list_id):
        yield from self.paginate(f"accounts/{account_id}/rules/lists/{list_id}/items")

    def add_rule_list_item(self, account_id, list_id, ip, commment=None):
        # docs: https://api.cloudflare.com/#rules-lists-create-list-items
        path = f"accounts/{account_id}/rules/lists/{list_id}/items"
        data = {"ip": ip}
        if commment:
            data["comment"] = commment

        response = self.request(path, data=[data], method="POST")
        return response["result"]

    def get_operation_status(self, account_id, operation_id):
        # docs: https://api.cloudflare.com/#rules-lists-get-bulk-operation
        path = f"accounts/{account_id}/rules/lists/bulk_operations/{operation_id}"
        return self.request(path)
