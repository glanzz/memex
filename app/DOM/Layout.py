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
    TOLERABLE_WIDTH_PERCENT_FOR_TEXT_BREAK,
    SOFT_HYPEN,
    FontFamily,
    BlockType,
)
from app.DOM import Text, Comment, Element


class FontCache:
    def __init__(self):
        self.cache = {}

    def get_font(self, weight, style, size, family):
        if not self.cache.get((weight, style, size, family)):
            font = TKFont.Font(
                family=family,
                size=size,
                weight=weight,
                slant=style,
            )
            self.cache[(weight, style, size, family)] = (font, Label(font=font))
        return self.cache[(weight, style, size, family)][0]


class Layout:
    __BLOCK_ELEMENTS = [
        "html", "body", "article", "section", "nav", "aside",
        "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
        "footer", "address", "p", "hr", "pre", "blockquote",
        "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
        "figcaption", "main", "div", "table", "form", "fieldset",
        "legend", "details", "summary"
    ]
    def __init__(self, node, width, height, previous, parent) -> None:
        self.node = node
        self.children = []
        self.previous = previous
        self.parent = parent

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
        self.caps = False
        self.pre = False
        self.family = FontFamily.DEFAULT.value

        self.line = []

    def layout(self):
        if not self.node:
            return
        mode = self.layout_mode()
        if mode == BlockType.BLOCK.name:
            previous = None
            for child in self.node.children:
                next = Layout(child, self.width, self.height, self, previous)
                self.children.append(next)
                previous = next
        else:
            if self.node:
                self.cursor_x = 0
                self.cursor_y = 0
                self.weight = "normal"
                self.style = "roman"
                self.size = 16

                self.line = []
                self.recurse(tree=self.node)
                self.flush()
        for child in self.children:
            child.layout()
        for child in self.children:
            self.display_list.extend(child.display_list)
        self.content_height = self.cursor_y

    def add_word(self, word):
        # Handle new line character
        font = self.font_cache.get_font(self.weight, self.style, self.size, self.family)

        if word == "" or (word == "\n"):
            self.flush()
            return

        if self.caps:
            word = word.upper()

        word_width = font.measure(word)

        if (self.cursor_x + word_width) > (self.width - HSTEP) and not self.pre:
            remaining_width = self.width - self.cursor_x - HSTEP
            if remaining_width > TOLERABLE_WIDTH_PERCENT_FOR_TEXT_BREAK * self.width:
                slice_index = self.get_slice_index_for_accomodation(
                    font, word, remaining_width
                )
                accomodable_text = self.__get_accomodable_text(word[: slice_index + 1])

                """Accomodate text add new line and insert remaining text by recursive call to add text"""
                self.add_word(accomodable_text)
                self.flush()
                self.add_word(word[slice_index + 1 :])
                return
            else:
                self.flush()
        self.line.append((self.cursor_x, word, font, self.script))
        self.cursor_x += word_width + font.measure(" ")

    def __get_accomodable_text(self, text):
        """Text shown with - after it as it breaks"""
        return f"{text}-"

    def get_slice_index_for_accomodation(self, font, text, width):
        if SOFT_HYPEN in text:
            """If soft hypen already available break at that point"""
            return text.find(SOFT_HYPEN)

        for i in range(len(text)):
            if font.measure(self.__get_accomodable_text(text[: i + 1])) >= width:
                return (
                    i - 1
                )  # Current index exceeds accomodable space so use next previous index
        return 0

    def flush(self):
        if not self.line:
            return
        max_ascent = max(
            [font.metrics("ascent") for x, word, font, super_script in self.line]
        )
        max_descent = max(
            [font.metrics("descent") for x, word, font, super_script in self.line]
        )

        baseline = self.cursor_y + (DEFAULT_LINE_HEIGHT * max_ascent)
        for x, word, font, script in self.line:
            self.display_list.append(
                (
                    x,
                    self.get_y(baseline, max_ascent, max_descent, font, script),
                    word,
                    font,
                )
            )

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

    def open_tag(self, tag):
        if tag == "i":
            self.style = FontStyle.ITALIC.value
        elif tag == "b":
            self.weight = FontWeight.BOLD.value

        elif tag == "big":
            self.size = FontSize.BIG.value

        elif tag == "small":
            self.size = FontSize.SMALL.value

        elif tag == "br/" or tag == "br":
            self.flush()
        elif tag == "sup":
            self.script = FontScript.SUPER.name
            self.size = self.size // 2

        elif tag == "sub":
            self.script = FontScript.SUB.name
            self.size = self.size // 2

        elif tag == "abbr":
            self.size = int(self.size / 1.5)
            self.caps = True
            self.weight = FontWeight.BOLD.value

        elif tag == "pre":
            self.pre = True
            self.family = FontFamily.COURIER_NEW.value
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = FontStyle.ROMAN.value
        elif tag == "b":
            self.weight = FontWeight.NORMAL.value
        elif tag == "big":
            self.size = FontSize.DEFAULT.value
        elif tag == "small":
            self.size = FontSize.DEFAULT.value
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "sup":
            self.script = FontScript.DEFAULT.name
            self.size = self.size * 2
        elif tag == "sub":
            self.script = FontScript.DEFAULT.name
            self.size = self.size * 2
        elif tag == "abbr":
            self.size = int(self.size * 1.5)
            self.caps = False
            self.weight = FontWeight.NORMAL.value
        elif tag == "pre":
            self.pre = False
            self.family = FontFamily.DEFAULT.value

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.add_word(word)
        elif isinstance(tree, Comment):
            # Skip comment for now but can be required in future
            return
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = Layout(child, self.width, self.height, self, previous)
            self.children.append(next)
            previous = next
    
    def layout_mode(self):
        if isinstance(self.node, Text):
            return BlockType.INLINE.name
        elif self.node and any([isinstance(child, Element) and child.tag in self.__BLOCK_ELEMENTS for child in self.node.children]):
            return BlockType.BLOCK.name
        elif self.node.children:
            return BlockType.INLINE.name
        else:
            return BlockType.BLOCK.name
    
