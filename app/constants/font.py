from enum import Enum


class FontWeight(Enum):
    NORMAL = "normal"
    BOLD = "bold"


class FontStyle(Enum):
    ITALIC = "italic"
    ROMAN = "roman"


class FontSize(Enum):
    DEFAULT = 14
    BIG = 16
    SMALL = 12


DEFAULT_LINE_HEIGHT = 1.25
