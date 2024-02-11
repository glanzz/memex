from app.config import DEBUG

class Logger:
  @classmethod
  def message(cls, message):
    print(message)
  
  @classmethod
  def error(cls, error):
    print(error)
  
  @classmethod
  def debug(cls, debug_message):
    if DEBUG:
      print(debug_message)
