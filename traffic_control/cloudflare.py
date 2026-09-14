import datetime
import json
import os
from dataclasses import dataclass
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

    def paginate(self, path, query_string=None, data=None, headers=None, method="get", row_class=dict, defaults=None):
        query_string = query_string or {}
        defaults = defaults or {}
        if issubclass(row_class, CloudflareResource):
            defaults["_api"] = self

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
                result.update(defaults)
                yield row_class(**result)

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
        yield from self.paginate("accounts", row_class=Account)

    def get_operation_status(self, account_id, operation_id):
        # TODO: move to Operation
        # docs: https://api.cloudflare.com/#rules-lists-get-bulk-operation
        path = f"accounts/{account_id}/rules/lists/bulk_operations/{operation_id}"
        return self.request(path)


def parse_datetime(value):
    if isinstance(value, datetime.datetime):
        return value
    elif isinstance(value, str):
        assert value[-1] == "Z"
        created_on = datetime.datetime.fromisoformat(value[:-1])
        return created_on.replace(tzinfo=datetime.timezone.utc)
    else:
        raise ValueError(f"Value {repr(value)} cannot be parted into datetime")


class CloudflareResource:
    pass


@dataclass
class Account(CloudflareResource):
    id: str
    name: str
    type: str
    settings: dict
    legacy_flags: dict
    created_on: datetime.datetime
    _api: Cloudflare = None

    def __post_init__(self):
        self.created_on = parse_datetime(self.created_on)

    def rules_lists(self):
        yield from self._api.paginate(f"accounts/{self.id}/rules/lists", row_class=RulesList, defaults={"account": self})


@dataclass
class RulesList(CloudflareResource):
    id: str
    name: str
    kind: str
    account: Account
    num_items: int
    num_referencing_filters: int
    created_on: datetime.datetime
    modified_on: datetime.datetime
    _api: Cloudflare = None

    def __post_init__(self):
        self.created_on = parse_datetime(self.created_on)
        self.modified_on = parse_datetime(self.modified_on)

    def items(self):
        yield from self._api.paginate(f"accounts/{self.account.id}/rules/lists/{self.id}/items")

    def add_items(self, ips, comment=None):
        # docs: https://api.cloudflare.com/#rules-lists-create-list-items
        path = f"accounts/{self.account.id}/rules/lists/{self.id}/items"
        comment = (comment or "").strip()
        data = [{"ip": ip, "comment": comment} for ip in ips]
        response = self._api.request(path, data=data, method="POST")
        # TODO: return Operation
        return response["result"]

    def delete_items(self, list_items_ids):
        # docs: https://api.cloudflare.com/#rules-lists-delete-list-items
        path = f"accounts/{self.account.id}/rules/lists/{self.id}/items"
        data = {"items": [{"id": id_} for id_ in list_items_ids]}
        response = self._api.request(path, data=data, method="DELETE")
        return response["result"]
