from app.DOM import Layout


class DocumentLayout:
    def __init__(self, node, width, height) -> None:
        self.node = node
        self.parent = None
        self.children = []
        self.width = width
        self.height = height

    def layout(self):
        child = Layout(
            self.node, width=self.width, height=self.height, parent=self, previous=None
        )
        self.children.append(child)
        child.layout()
        self.display_list = child.display_list
