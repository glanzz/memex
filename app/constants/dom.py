COMMENT_START = "<!--"
COMMENT_END = "-->"


from enum import Enum


class ParseContent(Enum):
    TEXT = 1
    SCRIPT = 2
