import socket
from app.constants import FORWARD_SLASH, CONTENT_TYPE, CONTENT_LENGTH
from app.schemes import BaseScheme

class HTTPScheme(BaseScheme):
  def __init__(self, url):
    super().__init__(url)
    self.socket = None
    

  def set_path(self):
    self.url = self.url + (FORWARD_SLASH if FORWARD_SLASH not in self.url else '')
    self.host, path = self.url.split(FORWARD_SLASH, 1)
    self.derive_port()
    self.path = FORWARD_SLASH + path
  
  def derive_port(self):
    self.port = 80
    self._get_user_specified_port()
    
  
  def _get_user_specified_port(self):
    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)

  def get_request_headers(self):
    headers = { "User-Agent": "memz-0.0", "Host": self.host, 'Content-type': 'utf-8'}
    header_string = ""
    for header in headers:
      header_string += f"{header}: {headers[header]}\r\n"
    return header_string
  
  def init_socket(self):
    return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
  
  def assign_socket(self):
    self.socket = self.init_socket()

  def get_socket(self) -> socket.socket:
    return self.socket

  def request(self):
    self.assign_socket()
    self.get_socket().connect((self.host, self.port))
    request_data = self.get_request_data()
    self.get_socket().send(request_data)

    response = self.get_socket().makefile("r", encoding="utf-8", newline="\r\n")
    statusline = response.readline()
    version, status, explaination = statusline.split(" ", 2)
    response_headers = self.get_response_headers(response=response)
    assert "transfer-encoding" not in response_headers
    assert "content-encoding" not in response_headers

    content_length = response_headers.get(CONTENT_LENGTH)
    content_length = int(content_length) if content_length != None else None

    self.body_encoding = self.get_body_encoding(response_headers.get(CONTENT_TYPE))
    self.body = response.read(content_length)
    self.get_socket().close()
  
  def get_response_headers(self, response):
    response_headers = {}
    while(True):
      header = response.readline()
      if(header == "\r\n"): break
      header_name, header_value = header.split(":", 1)
      response_headers[header_name.casefold()] = header_value.strip()
    return response_headers
  
  def get_request_data(self):
    return (f"GET {self.path} HTTP/1.1\r\n"
      + self.get_request_headers() +
      "\r\n").encode('utf-8')
