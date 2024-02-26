class Text:
    def __init__(self, text, parent) -> None:
        self.text = text
        self.parent = parent
        self.children = []
    
    def __repr__(self) -> str:
        return self.text

