class BaseScheme:
  '''
  All Schemes must extend base scheme and implement the
  request() which returns generates body and body_encoding
  '''
  def __init__(self, url):
    self.body_encoding = None
    self.body = None
    self.url = url
    self.set_path()

  def set_path(self):
      self.path = self.url

  def get_body_encoding(self, content_type):
    if content_type and ";" in content_type:
      content_type, encoding = content_type.split(";", 1)
      if encoding and "charset" in encoding:
        charset_param_name, encoding = encoding.split("=")
        return encoding.strip()
      return None

    return None
  
  def request(self):
    pass
