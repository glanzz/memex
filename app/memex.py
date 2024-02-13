from app.logger import Logger
from app.schemes import HTTPScheme
from app.constants import ENTITY_SYMBOL_MAPPING, DEFAULT_URL
from app.URL import URL
from app.Cache import Cache

class Memex:
  def __enter__(self):
    Cache.safe_init_folder()
    return Memex()

  def show(self, body, encoding, view_mode=False):
    show_data = body
    if encoding:
      show_data = body.encode('utf-8').decode(encoding)
    in_tag = False

    skip_till = None
    data_length = len(show_data)
    for i in range(data_length):
      if skip_till and i < skip_till:
        continue
        
      if view_mode:
        print(show_data[i], end="")
        continue

      if show_data[i] == "<":
        in_tag = True
      elif show_data[i] == ">":
        in_tag = False
      elif show_data[i] == "&":
        remaining_string = show_data[i+1:]
        if not remaining_string:
          print(show_data[i], end="")
          break
        token, remaining_string = remaining_string.split(";", 1)
        token_value = ENTITY_SYMBOL_MAPPING.get(token)
        if token_value:
          print(token_value, end="")
          if remaining_string == "":
            break
          skip_till = show_data.find(remaining_string)
        else:
          print(show_data[i], end="")
      elif not in_tag:
        print(show_data[i], end="")


  def load(self, url = DEFAULT_URL):
    url = URL(url=url if url else DEFAULT_URL)
    url.scheme_request.request()
    self.show(
      url.scheme_request.body,
      encoding=url.scheme_request.body_encoding,
      view_mode=url.get_view_mode()
    )
  
  def __exit__(self, *args):
    Logger.message("Closing all sockets...")
    HTTPScheme.close_sockets()
    Cache.write() # Persist cache details for further use
