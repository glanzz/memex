from app.constants import HSTEP, VSTEP
from app.DOM import Layout


class DocumentLayout:
    def __init__(self, node, width, height) -> None:
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.node = node
        self.parent = None
        self.children = []
        self.window_width = width
        self.window_height = height
        self.content_height = height  # Variable to hold whole of content height & no differnce between self.height for now

    def __repr__(self) -> str:
        return f"Document Layout node:{self.node} height:{self.height} width:{self.width} contentheight:{self.content_height} windowheight:{self.window_height} windowwidth:{self.window_width}"

    def layout(self):
        child = Layout(self.node, parent=self, previous=None)
        self.width = self.window_width - (
            2 * HSTEP
        )  # 2 HSTEPs is gutter space at the ends
        self.x = HSTEP
        self.y = VSTEP
        self.children.append(child)
        child.layout()
        self.height = (
            child.height
        )  # This value is set by accumlating all the previous values of children
        self.content_height = child.height
        self.display_list = child.display_list
