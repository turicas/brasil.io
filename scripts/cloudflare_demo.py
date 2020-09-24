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
    ips = ["8.8.8.8", "9.9.9.9"]

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
    print(f"Inserting demo ips: {ips}...")
    operation_info = cf.add_rule_list_items(account_id, list_id, ips)
    operation_id = operation_info["operation_id"]

    # Get async operation status
    status = cf.get_operation_status(account_id, operation_id)
    print(status)

    # Fetching all IPs to delete demo one
    print(f"Removing demo ips: {ips}...")
    list_items_ids = []
    for obj in cf.rules_list_items(account_id, list_id):
        if obj["ip"] in ips:
            list_items_ids.append(obj["id"])
        if len(list_items_ids) == len(ips):
            operation_info = cf.delete_rule_list_items(account_id, list_id, list_items_ids)
            status = cf.get_operation_status(account_id, operation_info["operation_id"])
            print(status)
            break

    print("FINISHED")
