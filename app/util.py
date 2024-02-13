import os
from app.constants import CACHE_INDEX_FILE_NAME, CACHE_FOLDER
def get_cache_index_file(directory):
  return os.path.join(directory, f"{CACHE_FOLDER}/{CACHE_INDEX_FILE_NAME}")

