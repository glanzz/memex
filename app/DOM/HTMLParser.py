from app.constants import ENTITY_SYMBOL_MAPPING
from app.DOM import Text, Element


class HTMLParser:
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

    def parse(self):
        buffer = ""
        show_data = (
            self.body.decode(self.encoding if self.encoding else "utf-8")
            if type(self.body) != "str"
            else self.body
        )
        in_tag = False

        skip_till = None
        data_length = len(show_data)
        for i in range(data_length):
            if skip_till and i < skip_till:
                continue

            if self.view_mode:
                buffer += show_data[i]
                continue

            if show_data[i] == "<":
                in_tag = True
                if buffer:
                    self.add_text(buffer)
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
                    if remaining_string == "":  # There is no content left after token
                        break
                    skip_till = show_data.find(
                        remaining_string
                    )  # Skip till the token code ends as its meaning is processed
                else:
                    buffer += show_data[i]
            else:
                buffer += show_data[i]

        if not in_tag and buffer:
            self.add_text(buffer)

        return self.finish()

    def add_text(self, text):
        if text.isspace():
            return  # Ignores whitespace texts
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def close_tag(self):
        node = self.unfinished.pop()
        parent = self.unfinished[-1]
        parent.children.append(node)

    def add_tag(self, tag):
        if tag.startswith("!"):
            return  # Ignore ! doctype and comments
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("/"):
            if len(self.unfinished) == 1:
                return
            self.close_tag()
        elif tag in self.__SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, parent)
            node.set_attributes(attributes=attributes)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, parent=parent)
            node.set_attributes(attributes=attributes)
            self.unfinished.append(node)

    def finish(self):
        while len(self.unfinished) > 1:
            self.close_tag()
        return self.unfinished.pop()

    @classmethod
    def print_tree(cls, node, indent=0):
        print(" " * indent, node)
        for child in node.children:
            cls.print_tree(child, indent=indent + 2)

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
