class Element:
    def __init__(self, tag, parent) -> None:
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = {}

    def __repr__(self) -> str:
        return f"<{self.tag}>"

    def set_attributes(self, attributes):
        self.attributes = attributes
