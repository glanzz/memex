import tkinter
from app.logger import Logger
from app.schemes import HTTPScheme
from app.constants import ENTITY_SYMBOL_MAPPING, DEFAULT_URL, WIDTH, HEIGHT, HSTEP, VSTEP, SCROLL_STEP
from app.URL import URL
from app.Cache import Cache


class Memex:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

    def __enter__(self):
        Cache.safe_init_folder()
        return Memex()
    
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()
    
    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
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
                text += show_data[i] #print(show_data[i], end="")
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
        content = self.show(
            url.scheme_request.body,
            encoding=url.scheme_request.body_encoding,
            view_mode=url.get_view_mode(),
        )
        self.layout(content=content)
        self.draw()
    
    def layout(self, content):
        self.layout_list = []
        cursor_x, cursor_y = HSTEP, VSTEP
        for c in content:
            self.layout_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP
            if cursor_x > WIDTH-HSTEP:
                cursor_x = HSTEP
                cursor_y += HSTEP
    
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.layout_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def __exit__(self, *args):
        Logger.message("Closing all sockets...")
        HTTPScheme.close_sockets()
        Cache.write()  # Persist cache details for further use
