from django.conf import settings

from traffic_control.cloudflare import Cloudflare


def run():
    """
    Demo script with Cloudflare API integration

    python manage.py runscript cloudflare_demo
    """
    email = settings.CLOUDFLARE_AUTH_EMAIL
    key = settings.CLOUDFLARE_AUTH_KEY
    desired_account_name = settings.CLOUDFLARE_ACCOUNT_NAME
    desired_list_name = settings.CLOUDFLARE_BLOCKED_IPS_RULE
    ip = "127.0.0.1"

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

    # Get list items
    for obj in cf.rules_list_items(account_id, list_id):
        print("rules list item", obj)

    # Insert ip into list item
    operation_info = cf.add_rule_list_item(account_id, list_id, ip)
    operation_id = operation_info["operation_id"]

    # Get async operation status
    status = cf.get_operation_status(account_id, operation_id)
    print(status)
