import gzip
import socket
from app.logger import Logger
from app.constants import (
    FORWARD_SLASH,
    CONTENT_TYPE,
    CONTENT_LENGTH,
    LOCATION,
    Schemes,
    MAX_REDIRECTION_COUNT,
    REDIRECTION_STATUS_RANGE,
    STATUS_CODE_OK,
    CACHE_CONTROL,
    DEFAULT_CACHE_TIME,
    CONTENT_ENCODING,
    ACCEPT_ENCODING,
    TRANSFER_ENCODING,
    GZIP,
)
from app.schemes import BaseScheme
from app.Cache import Cache


class HTTPScheme(BaseScheme):
    name = Schemes.HTTP.name
    # Caches the schemes socket used depth 1 key is host value name depth 2 key is port value
    # Eg: {"memex.com": {80: <socket1>, 443: <socket2>}}
    __SOCKET_POOL = {}
    __REDIRECTION_COUNT = 0

    def __init__(self, url, provider):
        super().__init__(url, provider)
        self.socket = None

    def set_path(self):
        self.url = self.url + (FORWARD_SLASH if FORWARD_SLASH not in self.url else "")
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
        headers = {
            "User-Agent": "memz-0.0",
            "Host": self.host,
            "Content-type": "utf-8",
            ACCEPT_ENCODING: "gzip",
        }
        header_string = ""
        for header in headers:
            header_string += f"{header}: {headers[header]}\r\n"
        return header_string

    # **** Pool Handling methods: START **** #
    def __add_to_socket_pool(self, socket: socket.socket):
        Logger.message("Adding socket to pool...")
        if not self.__SOCKET_POOL.get(self.host):
            self.__SOCKET_POOL[self.host] = {}
        if not self.__SOCKET_POOL[self.host].get(self.port):
            self.__SOCKET_POOL[self.host][self.port] = socket
        else:
            Logger.debug("Socket already cached !")

    def __get_socket_from_pool(self):
        if self.__SOCKET_POOL.get(self.host) and self.__SOCKET_POOL[self.host].get(
            self.port
        ):
            return self.__SOCKET_POOL[self.host][self.port]
        return None

    @classmethod
    def close_sockets(cls):
        """Reset connections on shutdown: Used by Main Engine Class"""
        for host_pool in cls.__SOCKET_POOL.values():
            for port_sockets in host_pool.values():
                port_sockets.close()
        cls.__SOCKET_POOL = {}  # Reset pool

    # **** Pool Handling methods: END **** #

    def reset_redirection_count(self):
        HTTPScheme.__REDIRECTION_COUNT = 0

    def allow_redirection_count(self):
        if HTTPScheme.__REDIRECTION_COUNT < MAX_REDIRECTION_COUNT:
            Logger.message("Redirecting...")
            HTTPScheme.__REDIRECTION_COUNT += 1
            return True
        Logger.error("Max Redirection Count reached!")
        self.reset_redirection_count()
        return False

    def init_socket(self):
        return socket.socket(
            family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
        )

    def assign_socket(self):
        existing_sock = self.__get_socket_from_pool()
        if not existing_sock:
            Logger.message("Creating new socket..")
            fresh_socket = self.init_socket()
            fresh_socket.connect((self.host, self.port))
            self.__add_to_socket_pool(socket=fresh_socket)
            self.socket = fresh_socket
        else:
            self.socket = existing_sock

    def get_socket(self) -> socket.socket:
        return self.socket

    @Cache.return_cached_request
    def request(self):
        self.assign_socket()
        request_data = self.get_request_data()
        Logger.debug(request_data)
        self.get_socket().sendall(request_data)

        response = self.get_socket().makefile("rb")
        statusline = response.readline().decode()
        version, status, explaination = statusline.split(" ", 2)
        status = int(status)
        response_headers = self.get_response_headers(response=response)

        if (
            REDIRECTION_STATUS_RANGE[0] <= status < REDIRECTION_STATUS_RANGE[1]
        ) and self.allow_redirection_count():
            self.redirection(response_headers=response_headers)
        else:
            self.body_encoding = self.get_body_encoding(
                response_headers.get(CONTENT_TYPE)
            )
            self.body = self.get_body(
                response=response, response_headers=response_headers
            )
            if (
                status == STATUS_CODE_OK
            ):  # Add check when supported request type more than GET: Allow only if request method is GET
                cache_control_header = response_headers.get(CACHE_CONTROL)
                self.cache_request(
                    file_content=self.body,
                    encoding_type=self.body_encoding,
                    cache_header=cache_control_header,
                )

    def construct_url(self):
        return f"{Schemes[self.name].value}://{self.host}:{self.port}{self.path}"

    def get_body(self, response, response_headers):
        transfer_encoding = response_headers.get(TRANSFER_ENCODING)
        content_length = response_headers.get(CONTENT_LENGTH)
        content_length = int(content_length) if content_length != None else None
        if transfer_encoding and "chunked" in transfer_encoding:
            body = self.get_chunked_body(response=response)
        else:
            body = response.read(content_length)
        body = self.decompress_content(body=body, response_headers=response_headers)

        return body

    def decompress_content(self, body, response_headers, transfer=False):
        content_encoding = response_headers.get(CONTENT_ENCODING)
        transfer_encoding = response_headers.get(TRANSFER_ENCODING)
        gzipped = (
            (transfer_encoding and GZIP in transfer_encoding)
            if transfer
            else (content_encoding and GZIP in content_encoding)
        )
        return gzip.decompress(body) if gzipped else body

    def get_chunked_body(self, response):
        chunk_val = b""
        while True:
            chunk_size = response.readline().decode(
                self.body_encoding if self.body_encoding else "utf-8"
            )
            if chunk_size == "\r\n":
                continue
            chunk_size = int(chunk_size, 16)
            if chunk_size == 0:
                break
            raw_chunk_value = response.read(chunk_size)
            try:
                chunk_val += raw_chunk_value
            except Exception as e:
                print(e)
                Logger.error("Could not decompress chunk")

        return chunk_val

    def cache_request(self, file_content, encoding_type, cache_header):
        cache_restrictions = {}
        if cache_header:
            cache_items = CACHE_CONTROL.split(",")
            for cache_item in cache_items:
                if "no-cache" in cache_item:
                    cache_restrictions["disable"] = True
                    break
                if "max-age" in cache_item:
                    cache_restrictions["cache_time"] = int(
                        cache_item.trim().replace("max-age=")
                    )
        if not cache_restrictions.get("disable"):
            Cache.cache_file(
                key=self.construct_url(),
                file_content=file_content,
                encoding_type=encoding_type,
                cache_time=cache_restrictions.get("cache_time", DEFAULT_CACHE_TIME),
            )

    def redirection(self, response_headers):
        redirection_location = response_headers[LOCATION]
        if redirection_location.startswith("/"):
            self.path = redirection_location
            self.request()
        else:
            redirection_provider = self.provider(url=redirection_location)
            redirection_provider.scheme_request.request()
            self.body_encoding = redirection_provider.scheme_request.body_encoding
            self.body = redirection_provider.scheme_request.body

    def get_response_headers(self, response):
        response_headers = {}
        while True:
            header = response.readline().decode()
            if header == "\r\n":
                break
            header_name, header_value = header.split(":", 1)
            response_headers[header_name.casefold()] = header_value.strip()
        return response_headers

    def get_request_data(self):
        return (
            f"GET {self.path} HTTP/1.1\r\n" + self.get_request_headers() + "\r\n"
        ).encode("utf-8")
