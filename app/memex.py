import tkinter
from app.logger import Logger
from app.schemes import HTTPScheme
from app.constants import (
    DEFAULT_URL,
    WIDTH,
    HEIGHT,
    VSTEP,
    SCROLL_STEP,
)
from app.URL import URL
from app.Cache import Cache
from app.DOM import Layout, HTMLParser


class Memex:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.window = tkinter.Tk()
        self.scrollbar = tkinter.Scrollbar(
            master=self.window,
            orient=tkinter.VERTICAL,
            background="#000000",
            elementborderwidth=2,
            command=self.handle_slide,
            activerelief=tkinter.SUNKEN,
            troughcolor="red",
        )
        self.canvas = tkinter.Canvas(
            master=self.window,
            width=self.width,
            height=self.height,
            yscrollcommand=self.scrollbar.set,
        )
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

        self.scroll = 0
        self.nodes = None
        # Mouse Events
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouse_scroll)

        # Resize Events
        self.window.bind("<Configure>", self.resize)

        # Initialize content height to default
        self.document = Layout(None, self.width, self.height, None, None)
        self.document.layout()

    def __enter__(self):
        Cache.safe_init_folder()
        return self

    def resize(self, e):
        if e.height > 1 and e.width > 1:
            self.height = e.height
            self.width = e.width
            self.document = Layout(self.nodes, self.width, self.height, None, None)
            self.document.layout()
            self.draw()

    def handle_slide(self, e, delta, unit=None):
        if self.height > 1 and self.width > 1:
            if e == tkinter.MOVETO:
                self.set_scroll(float(delta) * self.document.content_height)
                self.draw()
            elif e == tkinter.SCROLL:
                if unit == tkinter.PAGES:
                    self.set_scroll(self.scroll + (self.height * float(delta)))
                    self.draw()

    def set_slider(self):
        start_height = self.scroll / self.document.content_height
        current_height = self.height / self.document.content_height
        self.scrollbar.set(start_height, start_height + current_height)

    def get_scroll_max(self):
        return self.document.content_height - self.height

    def get_scroll_min(self):
        return 0

    def set_scroll(self, scroll):
        if scroll < self.get_scroll_min():
            self.scroll = self.get_scroll_min()
        elif scroll >= self.get_scroll_max():
            self.scroll = self.get_scroll_max()
        else:
            self.scroll = scroll
        self.set_slider()

    def scrolldown(self, e, delta=None):
        scroll_delta = -(delta) if delta else SCROLL_STEP
        if self.scroll > self.get_scroll_max():
            return
        self.set_scroll(self.scroll + scroll_delta)
        self.draw()

    def mouse_scroll(self, e):
        event_delta = e.delta
        (
            self.scrolldown(e, event_delta)
            if event_delta < 0
            else self.scrollup(e, event_delta)
        )

    def scrollup(self, e, delta=None):
        scroll_delta = delta if delta else SCROLL_STEP
        if self.scroll <= self.get_scroll_min():
            return
        self.set_scroll(self.scroll - scroll_delta)
        self.draw()

    def load(self, url=DEFAULT_URL):
        url = URL(url=url if url else DEFAULT_URL)
        url.scheme_request.request()
        self.nodes = HTMLParser(
            body=url.scheme_request.body,
            encoding=url.scheme_request.body_encoding,
            view_mode=url.get_view_mode(),
        ).parse()
        self.document = Layout(self.nodes, self.width, self.height, None, None)
        self.document.layout()
        self.draw()
        self.window.mainloop()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c, font in self.document.display_list:
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(
                x, y - self.scroll, text=c, font=font, anchor=tkinter.NW
            )

    def __exit__(self, *args):
        Logger.message("Closing all sockets...")
        HTTPScheme.close_sockets()
        Cache.write()  # Persist cache details for further use
