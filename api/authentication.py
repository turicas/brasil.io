from rest_framework.authentication import TokenAuthentication as BaseTokenAuth

from api.models import Token


class TokenAuthentication(BaseTokenAuth):
    model = Token
