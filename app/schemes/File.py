from app.schemes import BaseScheme

class FileScheme(BaseScheme):
  def request(self):
    with open(self.path, 'r') as request_data:
        self.body = request_data.read()

