from enum import Enum

FORWARD_SLASH = "/"
VIEW_SOURCE = {"name": "view-source", "prefix": "view-source:"}
DEFAULT_URL = "file://app/index.html"


class Schemes(Enum):
    HTTPS = "https"
    HTTP = "http"
    FILE = "file"
    DATA = "data"


ENTITY_SYMBOL_MAPPING = {
    "nbsp": "",
    "copy": "©cpp",
    "lt": "<",
    "gt": ">",
    "amp": "&",
}

MAX_REDIRECTION_COUNT = 2

REDIRECTION_STATUS_RANGE = (300, 400)
STATUS_CODE_OK = 200


GZIP = "gzip"
