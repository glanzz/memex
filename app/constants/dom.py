COMMENT_START = "<!--"
COMMENT_END = "-->"


from enum import Enum


class ParseContent(Enum):
    TEXT = 1
    SCRIPT = 2
    TAG_QUOTE = 3


class BlockType(Enum):
    INLINE = 1
    BLOCK = 2
