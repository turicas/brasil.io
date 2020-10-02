def clean_value(key, value):
    if value == "false":
        return key, False
    if value == "true":
        return key, True
    if value == "None":
        return f"{key}__isnull", True
    return key, value


def parse_querystring(querystring):
    query = querystring.copy()
    order_by = query.pop("order-by", [""])
    order_by = [field.strip().lower() for field in order_by[0].split(",") if field.strip()]
    search_query = query.pop("search", [""])[0]
    query = {key: value for key, value in query.items() if value}
    return query, search_query, order_by


class DynamicModelFilterProcessor:
    def __init__(self, filtering: dict, allowed_filters: list):
        self.filtering = filtering
        self.allowed_filters = allowed_filters

    @property
    def filters(self):
        return dict(
            clean_value(k, self.filtering[k])
            for k in self.filtering
            if k in self.allowed_filters and self.filtering[k] is not None
        )
