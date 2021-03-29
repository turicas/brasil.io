"""
TODO: relatar problema da issue de login
"""

def possible_usernames(username, email):
    """
    >>> possible_usernames('test@example.com', 'test@example.com')
    ('test', 'test', 'test_example')
    >>> possible_usernames('@test', 'test@example.com')
    ('test', 'test', 'test_example')
    >>> possible_usernames('test@', 'test@example.com')
    ('test', 'test', 'test_example')
    >>> possible_usernames('@test@', 'test@example.com')
    ('test', 'test', 'test_example')
    >>> possible_usernames('test@123', 'test@example.com')
    ('test_123', 'test', 'test_example')
    >>> possible_usernames('test@exampl.com', 'test@example.com')
    ('test', 'test', 'test_example')
    """
    username = username.strip()
    email = email.strip()

    if username.lower() == email.lower():
        username = username.split("@")[0]
    else:
        if username.startswith("@"):
            username = username[1:]
        if username.endswith("@"):
            username = username[:-1]
        if "@" in username:
            stop = username.find("@")
            before, after = username[:stop], username[stop + 1:]
            if "." in after:
                username = before
            else:
                username = "_".join(username.split("@"))

    email_parts = email.split("@")
    possible_2 = email_parts[0]
    possible_3 = email_parts[0] + "_" + email_parts[1].split(".")[0]
    return (username, possible_2, possible_3)


def migrate_usernames():
    # with open("/data/fixed-usernames.csv", mode="w") as fobj:
    # writer = csv.DictWriter(fobj, fieldnames=["old_username", "new_username", "email"])
    for user in User.objects.filter(username__contains="@"):
        possible = possible_usernames(user.username, user.email)
        changed = False
        for username in possible:
            if not User.objects.filter(username=username).exists():
                # writer.writerow(...)
                changed = True
                # TODO: save user.email in CSV
                # TODO: create script to send email
                #user.username = new
                #user.save()
                pass
        if not changed:
            print(f"Conflict in: {user.username} / {user.email} (would be: {new} but already exists)")
