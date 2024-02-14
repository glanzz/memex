import datetime
import time
import string
import random
import os
import json
from app.constants import CACHE_FOLDER, CACHE_FILE_NAME_LENGTH, DEFAULT_CACHE_TIME
from app.util import get_cache_index_file
from app.logger import Logger


class Cache:
    """
    Cache Structure:
    "url": {
        "expire": 1011,
        "name": "abc.html",
        "encoding_type": "utf-8"
      }
    """

    __DIR_NAME = os.path.dirname(__file__)
    __CACHE_INDEX = {}
    # __CACHE_INDEX = json.loads(open(get_cache_index_file(__DIR_NAME)) ) if os.path.isfile(get_cache_index_file(__DIR_NAME)) else {}

    @classmethod
    def safe_init_folder(cls):
        cache_folder = os.path.join(Cache.__DIR_NAME, CACHE_FOLDER)
        if not os.path.exists(cache_folder):
            os.mkdir(cache_folder)
        cache_file_name = os.path.join(get_cache_index_file(Cache.__DIR_NAME))
        if not os.path.isfile(cache_file_name):
            cls.write(mode="x")
        cls.load()  # debug

    @classmethod
    def retrieve_cache(cls, key):
        cache_info = cls.__CACHE_INDEX.get(key)
        body = None
        body_encoding = None
        if cache_info:
            Logger.debug("Cached data found !")
            if (
                datetime.datetime.utcfromtimestamp(cache_info["expire"])
                > datetime.datetime.utcnow()
            ):
                Logger.debug("Cached data valid !")
                body = b""
                with open(
                    cls.__get_file_path(file_name=cache_info["name"]), "rb"
                ) as cachefile:
                    body = cachefile.read()
                body_encoding = cache_info["encoding_type"]
            else:
                Logger.debug("Removing expired cache !")
                cls.invalidate(key)
        return body, body_encoding

    @classmethod
    def write(cls, mode="w"):
        with open(get_cache_index_file(Cache.__DIR_NAME), mode=mode) as cache_index:
            json.dump(Cache.__CACHE_INDEX, cache_index)

    @classmethod
    def load(cls):
        with open(get_cache_index_file(Cache.__DIR_NAME)) as index_file:
            Cache.__CACHE_INDEX = json.load(index_file)

    @classmethod
    def invalidate(cls, key):
        os.remove(cls.__get_file_path(cls.__CACHE_INDEX[key]["name"]))
        del cls.__CACHE_INDEX[key]
        cls.write()

    def generate_file_name():
        return "".join(random.choices(string.ascii_letters, k=CACHE_FILE_NAME_LENGTH))

    @classmethod
    def cache_file(
        self, key, file_content, encoding_type, cache_time=DEFAULT_CACHE_TIME
    ):
        Logger.debug("Caching data...")
        Logger.debug("Cache time:" + str(cache_time))
        if self.__CACHE_INDEX.get(key):
            Logger.error("Key already exists remove existing key")
            del self.__CACHE_INDEX[key]

        file_name = self.generate_file_name()
        date_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time)
        expire_time = int(time.mktime(date_time.timetuple()))
        with open(self.__get_file_path(file_name=file_name), "xb") as cache_file:
            cache_file.write(file_content)

        self.__CACHE_INDEX[key] = {
            "encoding_type": encoding_type,
            "expire": expire_time,
            "name": file_name,
        }
        Logger.debug(self.__CACHE_INDEX)

    def __get_file_path(file_name):
        return os.path.join(Cache.__DIR_NAME, CACHE_FOLDER + "/" + file_name)

    @classmethod
    def return_cached_request(cls, func):
        def verify_cache(*args, **kwargs):
            http_object = args[0]
            body, body_encoding = Cache.retrieve_cache(key=http_object.construct_url())
            # If body exists return use cached data else start the request
            if body:
                http_object.body = body
                http_object.body_encoding = body_encoding
                return
            return func(*args, **kwargs)

        return verify_cache
