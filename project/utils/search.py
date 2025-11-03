from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank

# TODO: we may want to get the available languages by running the query in the current database
# Mapping created from joining results of `SELECT cfgname FROM pg_ts_config`
# and the table found in <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>
ISO_639_1_TO_POSTGRES = {
    None: "simple",
    "ar": "arabic",
    "hy": "armenian",
    "eu": "basque",
    "ca": "catalan",
    "da": "danish",
    "nl": "dutch",
    "en": "english",
    "fi": "finnish",
    "fr": "french",
    "de": "german",
    "el": "greek",
    "hi": "hindi",
    "hu": "hungarian",
    "id": "indonesian",
    "ga": "irish",
    "it": "italian",
    "lt": "lithuanian",
    "ne": "nepali",
    "no": "norwegian",
    "pt": "portuguese",
    "ro": "romanian",
    "ru": "russian",
    "sr": "serbian",
    "es": "spanish",
    "sv": "swedish",
    "ta": "tamil",
    "tr": "turkish",
    "yi": "yiddish",
}
AVAILABLE_LANGUAGES = set(ISO_639_1_TO_POSTGRES.values())


class SearchQuerySetMixin:
    def search(self, search_vector, term, language, normalization=8 + 32, headline_expression=None, min_rank=None):
        """Executes a full-text search (if `term` is not empty)

        [`normalization`](https://www.postgresql.org/docs/current/textsearch-controls.html#TEXTSEARCH-RANKING) can
        speed up the search execution and enhance ranking:
        - 0 (the default) ignores the document length
        - 1 divides the rank by 1 + the logarithm of the document length
        - 2 divides the rank by the document length
        - 4 divides the rank by the mean harmonic distance between extents (this is implemented only by ts_rank_cd)
        - 8 divides the rank by the number of unique words in document
        - 16 divides the rank by 1 + the logarithm of the number of unique words in document
        - 32 divides the rank by itself + 1
        `search_vector` is the expression which constructs the search vector. If you have a `SearchVectorField` in your
        model, you could just pass `django.db.models.F("my_vector_field")`. If not, you could use
        `django.contrib.postgres.search.SearchVector("field1", ..., "fieldN", config="language")` (in tihs last option
        make sure you have a `GinIndex` with that same expression.
        `headline_expression` is used to returns highlighted search results. Must be a text field name or an
        expression to be used to extract the snippet from.
        """
        if not term:  # `qs.search(..., None, ...)` = `qs` (shortcut)
            return self
        elif language not in AVAILABLE_LANGUAGES:
            raise ValueError(f"Unknown language for postgres: {repr(language)}")

        config = f"pg_catalog.{language}"
        query = SearchQuery(term, config=config, search_type="websearch")
        qs = self.filter(search_vector=query)
        qs = qs.annotate(search_rank=SearchRank(search_vector, query, normalization=normalization))
        if headline_expression:
            qs = qs.annotate(
                headline=SearchHeadline(
                    headline_expression,
                    query,
                    config=config,
                    start_sel="<span class='term'>",
                    stop_sel="</span>",
                ),
            )
        if min_rank is not None:
            qs = qs.filter(search_rank__gte=min_rank)

        # Overwriting `qs.query.order_by` to APPEND ordering field instead of OVERWRITTING (as in `qs.order_by`). We
        # append directly (instead of using `qs.query.add_ordering` because the search rank must have precedence over
        # the other ordering.
        qs.query.order_by = tuple(["-search_rank"] + list(qs.query.order_by))
        return qs

    def order_by(self, *args, **kwargs):
        # We must force search_rank ordering, since some operations will add ordering after calling `.search` (like in
        # Django Admin)
        qs = super().order_by(*args, **kwargs)
        if "-search_rank" in qs.query.order_by and qs.query.order_by[0] != "-search_rank":
            qs.query.order_by = tuple(["-search_rank"] + [item for item in qs.query.order_by if item != "-search_rank"])
        return qs
