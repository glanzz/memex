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

class FontScript(Enum):
  DEFAULT = 0
  SUPER = 1
  SUB = 2


DEFAULT_LINE_HEIGHT = 1.25
