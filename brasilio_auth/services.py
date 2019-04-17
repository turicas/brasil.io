from brasilio_auth.models import NewsletterSubscriber


def subscribers_as_csv_rows(include_header=True):
    rows = []
    if include_header:
        rows.append(('name','email'))

    qs = NewsletterSubscriber.objects.select_related('user')
    for user in [subscriber.user for subscriber in qs]:
        rows.append((user.get_full_name(), user.email))

    return rows
