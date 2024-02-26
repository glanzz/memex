class Comment:
    def __init__(self, comment, parent) -> None:
        self.comment = comment
        self.parent = parent

    def __repr__(self) -> str:
        return "<!--" + self.comment + "-->"
