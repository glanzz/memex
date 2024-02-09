from app.schemes import HTTPSScheme, HTTPScheme, FileScheme, DataScheme
from app.constants import Schemes, VIEW_SOURCE

class URL:
  def __init__(self, url):
    self.url = url
    self.set_view_mode()
    self.set_scheme()
    self.scheme_request = self.get_scheme_request_handler()(self.url)
  
  def get_scheme_request_handler(self):
    if self.scheme == Schemes.HTTP.value:
      return HTTPScheme
    elif self.scheme == Schemes.HTTPS.value:
      return HTTPSScheme
    elif self.scheme == Schemes.FILE.value:
      return FileScheme
    elif self.scheme == Schemes.DATA.value:
      return DataScheme
    else:
      raise Exception("Unimplemented Scheme")

  def set_scheme(self):
    if self.url.startswith(DataScheme.PREFIX):
      self.scheme = Schemes.DATA.value
    else:
      self.scheme, self.url = self.url.split("://", 1)
      self.url = self.url.lower()
    assert self.scheme in [scheme.value for scheme in Schemes]
  
  def set_view_mode(self):
    if self.url.startswith(VIEW_SOURCE["prefix"]):
      self.url = self.url.replace(VIEW_SOURCE["prefix"], "", 1)
      self.view_mode = True
    else:
      self.view_mode = False

  def get_view_mode(self):
    return self.view_mode

    
