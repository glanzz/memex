import base64
import ssl
import socket
from constant import FORWARD_SLASH, HTTP, HTTPS, FILE, DATA, DEFAULT_URL, ENTITY_SYMBOL_MAPPING, VIEW_SOURCE
from headers import CONTENT_TYPE

class URL:
  def __init__(self, url):
    self.view_mode = False
    if url.startswith("data:"):
      self.scheme = DATA
      self.path = url
      return
    elif url.startswith("view-source:"):
      url = url.replace("view-source:", "", 1)
      self.view_mode = True

    self.scheme, url = url.split("://", 1)

    assert self.scheme in [HTTP.lower(), HTTPS.lower(), FILE.lower()]
    if self.scheme == FILE:
      self.path = url
    else:
      url = url + (FORWARD_SLASH if FORWARD_SLASH not in url else '')
      self.host, path = url.split(FORWARD_SLASH, 1)
      self.derive_port()
      self.path = FORWARD_SLASH + path
  
  def is_view_mode(self):
    return self.view_mode

  def derive_port(self):
    if self.scheme == HTTP:
      self.port = 80
    if self.scheme == HTTPS:
      self.port = 443
    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)
    
  def get_request_headers(self):
    headers = {"Connection": "close", "User-Agent": "memz-0.0", "Host": self.host, 'Content-type': 'utf-16'}
    header_string = ""
    for header in headers:
      header_string += f"{header}: {headers[header]}\r\n"
    return header_string

  def request(self):
    body_encoding = None
    if self.scheme == DATA:
      '''data:[<mediatype>][;base64],<data>'''
      self.path = self.path.split("data:", 1)[1]
      meta_data, data = self.path.split(",", 1)
      meta_data = meta_data if meta_data else "text/plain;charset=US-ASCII"
      if meta_data.endswith(";base64"):
        meta_data = meta_data.replace(";base64", "")
        data = base64.b64decode(data).decode()

      body_encoding = self.get_body_encoding(meta_data)
      body = data


    if self.scheme == FILE:
      with open(self.path, 'r') as request_data:
        body = request_data.read()

    if self.scheme in [HTTP, HTTPS]:
      sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
      if self.scheme == HTTPS:
        ctx = ssl.create_default_context()
        sock = ctx.wrap_socket(sock=sock, server_hostname=self.host)
      sock.connect((self.host, self.port))
      request_data = (f"GET {self.path} HTTP/1.0\r\n"
        + self.get_request_headers() +
        "\r\n").encode('utf-8')
      sock.send(request_data)
      response = sock.makefile("r", encoding="utf-8", newline="\r\n")
      statusline = response.readline()
      version, status, explaination = statusline.split(" ", 2)
      response_headers = {}
      while(True):
        header = response.readline()
        if(header == "\r\n"): break
        header_name, header_value = header.split(":", 1)
        response_headers[header_name.casefold()] = header_value.strip()
      assert "transfer-encoding" not in response_headers
      assert "content-encoding" not in response_headers
      body_encoding = self.get_body_encoding(response_headers.get(CONTENT_TYPE))
      body = response.read()
      sock.close()

    return body_encoding, body
  
  def get_body_encoding(self, content_type):
    if content_type and ";" in content_type:
      content_type, encoding = content_type.split(";", 1)
      if encoding and "charset" in encoding:
        charset_param_name, encoding = encoding.split("=")
        return encoding.strip()
      return None

    return None



    
def show(body, encoding, is_view_mode=False):
  show_data = body
  if encoding:
    show_data = body.encode('utf-8').decode(encoding)
  in_tag = False

  skip_till = None
  data_length = len(show_data)
  for i in range(data_length):
    if skip_till and i < skip_till:
      continue
      
    if is_view_mode:
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
    

def load(url):
  encoding, body = url.request()
  show(body, encoding=encoding, view_mode=url.is_view_mode())


if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL))
