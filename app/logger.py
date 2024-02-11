from app.config import DEBUG

class Logger:
  @classmethod
  def message(cls, message):
    '''Message to be visible even when debug is off'''
    print(message)
  
  @classmethod
  def error(cls, error):
    '''Error which requires attention shows even if debug is off'''
    print(error)
  
  @classmethod
  def debug(cls, debug_message):
    '''Use only for development purpose: Shown only on debug mode'''
    if DEBUG:
      print(debug_message)
