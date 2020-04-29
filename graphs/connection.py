from py2neo import authenticate, Graph as Py2NeoGraph

from django.conf import settings

graph_kwargs = {
    "host": settings.NEO4J_CONF["HOST"],
    "http_port": settings.NEO4J_CONF["PORT"],
    "bolt_port": settings.NEO4J_BOLT_PORT,
}

if settings.NEO4J_CONF["SCHEME"] == "https":
    graph_kwargs.update({"secure": True, "https_port": settings.NEO4J_CONF["PORT"]})
    del graph_kwargs["http_port"]

username, password = settings.NEO4J_CONF["USERNAME"], settings.NEO4J_CONF["PASSWORD"]
if username or password:
    authenticate("{}:{}".format(settings.NEO4J_CONF["HOST"], settings.NEO4J_CONF["PORT"]), username, password)
    graph_kwargs.update({"user": username, "password": password})


def get_graph_db_connection():
    if not getattr(get_graph_db_connection, "_open_conn", None):
        get_graph_db_connection._open_conn = Py2NeoGraph(**graph_kwargs)
    return get_graph_db_connection._open_conn
