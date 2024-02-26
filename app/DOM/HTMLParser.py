from app.constants import (
    ENTITY_SYMBOL_MAPPING,
    COMMENT_START,
    COMMENT_END,
    ParseContent,
)
from app.DOM import Text, Element, Comment


class HTMLParser:
    __HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]
    __SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def __init__(self, body, encoding, view_mode=False) -> None:
        self.body = body
        self.encoding = encoding
        self.view_mode = view_mode
        self.unfinished = []
        self.type = ParseContent.TEXT.name

    def parse(self):
        buffer = ""
        show_data = (
            self.body.decode(self.encoding if self.encoding else "utf-8")
            if type(self.body) != "str"
            else self.body
        )
        in_tag = False
        tag_quote = "" # Determines if the currently under quoted attribute of the tag
        in_comment = False

        skip_till = None
        data_length = len(show_data)
        for i in range(data_length):
            if skip_till and i < skip_till:
                continue

            if self.view_mode:
                buffer += show_data[i]
                continue

            if self.type == ParseContent.SCRIPT.name:
                if (
                    show_data[i] == "<"
                    and data_length >= i + 8
                    and show_data[i + 1 : i + 9] == "/script>"
                ):
                    if buffer:
                        self.add_text(buffer)
                    self.add_tag("/script")
                    skip_till = i + 8
                else:
                    buffer += show_data[i]

            elif self.type == ParseContent.TAG_QUOTE.name:
              if show_data[i] == tag_quote:
                tag_quote = ""
                self.type = ParseContent.TEXT.name
              buffer += show_data[i]

            else:
                if show_data[i] == "<":
                    in_tag = True
                    if buffer:
                        self.add_text(buffer)
                    if (
                        data_length >= i + 3
                        and show_data[i + 1 : i + 4] == COMMENT_START[1:]
                    ):
                        in_comment = True
                        skip_till = i + 3
                    buffer = ""

                elif in_comment and show_data[i] == COMMENT_END[0]:
                    if (
                        data_length >= i + 2
                        and show_data[i + 1 : i + 3] == COMMENT_END[1:]
                    ):
                        if buffer:
                            self.add_comment(buffer)
                        in_comment = False
                        skip_till = i + 2
                        buffer = ""

                elif show_data[i] == ">":
                    in_tag = False
                    if buffer:
                        self.add_tag(buffer)
                    buffer = ""

                elif show_data[i] == "&":
                    remaining_string = show_data[i + 1 :]
                    if not remaining_string:  # Whole content ends with &
                        buffer += show_data[i]
                        break

                    splitlist = remaining_string.split(";", 1)
                    token = splitlist[0]
                    if (
                        len(splitlist) > 1
                    ):  # Check if there is anything remaining the token (Especially in cases where there is no ; after &)
                        remaining_string = splitlist[1]

                    token_value = ENTITY_SYMBOL_MAPPING.get(token)
                    if token_value:
                        buffer += token_value
                        if (
                            remaining_string == ""
                        ):  # There is no content left after token
                            break
                        skip_till = show_data.find(
                            remaining_string
                        )  # Skip till the token code ends as its meaning is processed
                    else:
                        buffer += show_data[i]

                else:
                    if in_tag and show_data[i] in ["'", '"']:
                      '''If in_tag and quote is found then consider remaining as quote and store current quote'''
                      self.type = ParseContent.TAG_QUOTE.name
                      tag_quote = show_data[i]

                    buffer += str(show_data[i])

        if not in_tag and buffer:
            self.add_text(buffer)

        return self.finish()

    def add_text(self, text):
        if text.isspace():
            return  # Ignores whitespace texts
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_comment(self, comment):
        if comment.isspace():
            return  # Ignores whitespace texts
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Comment(comment=comment, parent=parent)
        parent.children.append(node)

    def close_tag(self):
        node = self.unfinished.pop()
        parent = self.unfinished[-1]
        parent.children.append(node)

    def add_tag(self, tag):
        if tag.startswith("!"):
            return  # Ignore ! doctype and comments
        tag, attributes = self.get_attributes(tag)
        self.implicit_tags(tag)
        if tag.startswith("/"):
            if tag[1:] == "script":
                self.type = ParseContent.TEXT.name

            if len(self.unfinished) == 1:
                return
            self.close_tag()
        elif tag in self.__SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, parent)
            node.set_attributes(attributes=attributes)
            parent.children.append(node)
        else:
            if tag == "script":
                self.type = ParseContent.SCRIPT.name
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent=parent)
            node.set_attributes(attributes=attributes)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            self.close_tag()
        return self.unfinished.pop()

    @classmethod
    def print_tree(cls, node, indent=0):
        print(" " * indent, node)
        for child in node.children:
            cls.print_tree(child, indent=indent + 2)

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["/html", "head", "body"]:
                if tag in self.__HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif (
                open_tags == ["html", "head"]
                and tag not in ["/head"] + self.__HEAD_TAGS
            ):
                self.add_tag("/head")
            else:
                break

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}
        if len(parts) > 1:
            for attribute in parts[1:]:
                if "=" in attribute:
                    key, value = attribute.split("=", 1)
                    if len(value) > 2 and value[0] in ["'", '"']:
                        value = value[1:-1]
                    attributes[key.casefold()] = value
                else:
                    attributes[attribute.casefold()] = (
                        ""  # For attribute like required / disabled
                    )
        return tag, attributes
