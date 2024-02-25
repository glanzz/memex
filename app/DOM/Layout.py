from tkinter import font as TKFont
from tkinter import Label
from app.constants import (
    HSTEP,
    VSTEP,
    FontStyle,
    FontWeight,
    DEFAULT_LINE_HEIGHT,
    FontSize,
    FontScript,
)
from app.DOM import Text


class FontCache:
    def __init__(self):
        self.cache = {}

    def get_font(self, weight, style, size):
        if not self.cache.get((weight, style, size)):
            font = TKFont.Font(
                family="Helvetica",
                size=size,
                weight=weight,
                slant=style,
            )
            self.cache[(weight, style, size)] = (font, Label(font=font))
        return self.cache[(weight, style, size)][0]


class Layout:
    def __init__(self, tokens, width, height) -> None:
        self.display_list = []
        self.font_cache = FontCache()

        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.height = height
        self.width = width
        self.content_height = self.height
        self.weight = FontWeight.NORMAL.value
        self.style = FontStyle.ROMAN.value
        self.size = FontSize.DEFAULT.value
        self.script = FontScript.DEFAULT.name

        self.line = []

        self.generate_layout(tokens)

    def generate_layout(self, tokens):
        for token in tokens:
            self.token(token=token)
        self.flush()
        self.content_height = self.cursor_y

    def add_word(self, word):
        # Handle new line character
        font = self.font_cache.get_font(self.weight, self.style, self.size)

        if word == "" or (word == "\n"):
            self.flush()
            return

        word_width = font.measure(word)
        if (self.cursor_x + word_width) > (self.width - HSTEP):
            self.flush()
        self.line.append((self.cursor_x, word, font, self.script))
        self.cursor_x += word_width + font.measure(" ")

    def flush(self):
        if not self.line:
            return
        max_ascent = max([font.metrics("ascent") for x, word, font, super_script in self.line])
        max_descent = max([font.metrics("descent") for x, word, font, super_script in self.line])

        baseline = self.cursor_y + (DEFAULT_LINE_HEIGHT * max_ascent)
        for x, word, font, script in self.line:
            self.display_list.append((x, self.get_y(baseline, max_ascent, max_descent, font, script), word, font))

        self.cursor_y = baseline + (DEFAULT_LINE_HEIGHT * max_descent)
        self.cursor_x = HSTEP
        self.line = []
    
    def get_y(self, baseline, max_ascent, max_descent, font, script):
      y = baseline - font.metrics("ascent")
      if script == FontScript.SUPER.name:
        y = baseline - max_ascent
      elif script == FontScript.SUB.name:
        y = baseline + max_descent
      return y

    def token(self, token):
        if isinstance(token, Text):
            for word in token.text.split():
                self.add_word(word=word)
        elif token.tag == "i":
            self.style = FontStyle.ITALIC.value
        elif token.tag == "/i":
            self.style = FontStyle.ROMAN.value
        elif token.tag == "b":
            self.weight = FontWeight.BOLD.value
        elif token.tag == "/b":
            self.weight = FontWeight.NORMAL.value
        elif token.tag == "big":
            self.size = FontSize.BIG.value
        elif token.tag == "/big":
            self.size = FontSize.DEFAULT.value
        elif token.tag == "small":
            self.size = FontSize.SMALL.value
        elif token.tag == "/small":
            self.size = FontSize.DEFAULT.value
        elif token.tag == "br/" or token.tag == "br":
            self.flush()
        elif token.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
        elif token.tag == "sup":
            self.script = FontScript.SUPER.name
            self.size = self.size // 2
        elif token.tag == "/sup":
            self.script = FontScript.DEFAULT.name
            self.size = self.size * 2
        elif token.tag == "sub":
            self.script = FontScript.SUB.name
            self.size = self.size // 2
        elif token.tag == "/sub":
            self.script = FontScript.DEFAULT.name
            self.size = self.size * 2
