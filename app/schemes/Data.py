import base64
from app.schemes import BaseScheme


class DataScheme(BaseScheme):
  PREFIX = "data:"
  def request(self):
    '''data:[<mediatype>][;base64],<data>'''
    self.path = self.path.split("data:", 1)[1]
    meta_data, data = self.path.split(",", 1)
    meta_data = meta_data if meta_data else "text/plain;charset=US-ASCII"
    if meta_data.endswith(";base64"):
      meta_data = meta_data.replace(";base64", "")
      data = base64.b64decode(data).decode()

    self.body_encoding = self.get_body_encoding(meta_data)
    self.body = data
