def clean_value(key, value):
    if value == "None":
        return f"{key}__isnull", True
    return key, value


def parse_query_value(value):
    if str(value).lower() in ["false", "f"]:
        return False
    if str(value).lower() in ["true", "t"]:
        return True
    return value


def parse_querystring(querystring):
    query = {
        key: parse_query_value(value) for key, value in querystring.items() if value
    }
    order_by = query.pop("order-by", [""])
    order_by = [
        field.strip().lower() for field in order_by[0].split(",") if field.strip()
    ]
    search_query = query.pop("search", [""])[0]
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
