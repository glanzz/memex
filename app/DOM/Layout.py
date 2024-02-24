import tkinter.font as TKFont
from app.constants import HSTEP, VSTEP, FontStyle, FontWeight, DEFAULT_LINE_HEIGHT
from app.DOM import Text

class FontCache:
  def __init__(self):
    self.cache = {}
  
  def get_font(self, weight, style):
    if not self.cache.get((weight, style)):
      self.cache[(weight, style)] = TKFont.Font(
        size=16,
        weight=weight,
        slant=style,
      )
    return self.cache[(weight, style)]

    

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
      self.size = 16
      self.generate_layout(tokens)

  def generate_layout(self, tokens):
    for token in tokens:
        self.token(token=token)
    self.content_height = self.cursor_y
  

  def add_word(self, word):
    # Handle new line character
    if not word or (word == "\n"):
        self.cursor_y += font.metrics("linespace") * DEFAULT_LINE_HEIGHT
        self.cursor_x = HSTEP
        return

    font = self.font_cache.get_font(self.weight, self.style)
    

    word_width = font.measure(word)             
    if self.cursor_x + word_width > self.width - HSTEP:
        self.cursor_x = HSTEP
        self.cursor_y += font.metrics("linespace") * DEFAULT_LINE_HEIGHT
    self.display_list.append((self.cursor_x, self.cursor_y, word, font))
    self.cursor_x += (word_width + font.measure(" ")) # Add word and a space

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


