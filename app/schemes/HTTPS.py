import ssl
from app.schemes import HTTPScheme

class HTTPSScheme(HTTPScheme):
  def derive_port(self):
    self.port = 443
    self._get_user_specified_port()

  def init_socket(self):
    socket = super().init_socket()
    ssl_context = ssl.create_default_context()
    return ssl_context.wrap_socket(sock=socket, server_hostname=self.host)
