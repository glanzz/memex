import tkinter
from app.logger import Logger
from app.schemes import HTTPScheme
from app.constants import (
    ENTITY_SYMBOL_MAPPING,
    DEFAULT_URL,
    WIDTH,
    HEIGHT,
    HSTEP,
    VSTEP,
    SCROLL_STEP,
)
from app.URL import URL
from app.Cache import Cache


class Memex:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.window = tkinter.Tk()
        self.scrollbar = tkinter.Scrollbar(
            self.window,
            orient=tkinter.VERTICAL,
            background="#000000",
            elementborderwidth=2,
            command=self.handle_slide,
            activerelief=tkinter.SUNKEN,
            troughcolor="red",
        )
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height,
            yscrollcommand=self.scrollbar.set,
        )
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)

        self.scroll = 0
        self.content = ""
        # Mouse Events
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouse_scroll)

        # Resize Events
        self.window.bind("<Configure>", self.resize)

        # Initialize content height to default
        self.contentHeight = HEIGHT

    def __enter__(self):
        Cache.safe_init_folder()
        return Memex()

    def resize(self, e):
        if e.height > 1 and e.width > 1:
            self.height = e.height
            self.width = e.width
            self.layout()
            self.draw()

    def handle_slide(self, e, delta, unit=None):
        if self.height > 1 and self.width > 1:
            if e == tkinter.MOVETO:
                self.set_scroll(float(delta) * self.contentHeight)
                self.draw()
            elif e == tkinter.SCROLL:
                if unit == tkinter.PAGES:
                    self.set_scroll(self.scroll + (self.height * float(delta)))
                    self.draw()

    def set_slider(self):
        start_height = self.scroll / self.contentHeight
        current_height = self.height / self.contentHeight
        self.scrollbar.set(start_height, start_height + current_height)

    def get_scroll_max(self):
        return self.contentHeight - self.height

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

    def show(self, body, encoding, view_mode=False):
        text = ""
        show_data = body.decode(encoding if encoding else "utf-8")
        in_tag = False

        skip_till = None
        data_length = len(show_data)
        for i in range(data_length):
            if skip_till and i < skip_till:
                continue

            if view_mode:
                text += show_data[i]  # print(show_data[i], end="")
                continue

            if show_data[i] == "<":
                in_tag = True
            elif show_data[i] == ">":
                in_tag = False
            elif show_data[i] == "&":
                remaining_string = show_data[i + 1 :]
                if not remaining_string:
                    text += show_data[i]
                    break
                token, remaining_string = remaining_string.split(";", 1)
                token_value = ENTITY_SYMBOL_MAPPING.get(token)
                if token_value:
                    text += token_value
                    if remaining_string == "":
                        break
                    skip_till = show_data.find(remaining_string)
                else:
                    text += show_data[i]
            elif not in_tag:
                text += show_data[i]
        return text

    def load(self, url=DEFAULT_URL):
        url = URL(url=url if url else DEFAULT_URL)
        url.scheme_request.request()
        self.content = self.show(
            url.scheme_request.body,
            encoding=url.scheme_request.body_encoding,
            view_mode=url.get_view_mode(),
        )
        self.layout()
        self.draw()
        tkinter.mainloop()

    def layout(self):
        self.layout_list = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in self.content:
            # Handle new line character
            if c == "\n":
                cursor_y += VSTEP
                continue

            self.layout_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x > self.width - HSTEP:
                cursor_x = HSTEP
                cursor_y += VSTEP

        self.contentHeight = cursor_y  # Set content height to last value of cursor Y

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.layout_list:
            if y > self.scroll + self.height:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def __exit__(self, *args):
        Logger.message("Closing all sockets...")
        HTTPScheme.close_sockets()
        Cache.write()  # Persist cache details for further use
