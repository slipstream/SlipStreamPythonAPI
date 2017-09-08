"""
HTTP session via cookie jar implemented over `requests`.
"""

import os
import re
import stat
import socket
import requests
import logging
import time
from random import random
from threading import Lock

from requests.cookies import MockRequest
from six.moves.urllib.parse import urlparse
from six.moves.http_cookiejar import MozillaCookieJar
from six.moves.http_client import HTTPConnection, BadStatusLine, HTTPException
import sseclient

from .defaults import DEFAULT_COOKIE_FILE
from .exceptions import AbortException, \
    NotYetSetException, TerminalStateException, TooManyRequestsError, \
    NotFoundError, ServiceUnavailableError, ServerError, ClientError
from .log import get_logger

HEADER_SSE = 'text/event-stream'
HTTP_CONNECT_TIMEOUT = 0.1
HTTP_READ_TIMEOUT = 5.0
HTTP_TIMEOUTS = (HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT)

# Client Errors
NOT_FOUND_ERROR = 404
CONFLICT_ERROR = 409
PRECONDITION_FAILED_ERROR = 412
EXPECTATION_FAILED_ERROR = 417
TOO_MANY_REQUESTS_ERROR = 429

# Server Errors
SERVICE_UNAVAILABLE_ERROR = 503
BAD_GATEWAY_ERROR = 502


def init_http_logging(log_level, http_detail=False):
    requests_log = get_logger("requests.packages.urllib3")
    requests_log.setLevel(log_level)
    requests_log.propagate = True

    if http_detail and logging.DEBUG == log_level:
        HTTPConnection.debuglevel = 3
    else:
        HTTPConnection.debuglevel = 0


def has_key(_dict, key):
    """Case insensitive search for a key in a map.
    """
    return any(map(lambda k: re.match('%s$' % key, k, re.I), _dict))


def accept_in_headers(headers):
    return has_key(headers, 'accept')


def set_stream_header(headers):
    if accept_in_headers(headers):
        for k, v in headers.items():
            if re.match('accept$', k, re.IGNORECASE):
                headers[k] = '%s, %s' % (v, HEADER_SSE)
                break
    else:
        headers.update({'Accept': HEADER_SSE})
    return headers


def is_streamed_response(resp):
    """Streamed response is the one that
    - is successful, and
    - contains `HEADER_SSE` in the `accept` header.
    :param resp: `requests.models.Response`
    :return: bool
    """
    if resp and resp.ok and accept_in_headers(resp.request.headers):
        accept = ''
        for k, v in resp.request.headers.items():
            if re.match('accept$', k, re.IGNORECASE):
                accept = v
                break
        return re.search(HEADER_SSE, accept) is not None
    else:
        return False


class SessionStore(requests.Session):
    """A ``requests.Session`` subclass implementing a file-based session store.
    """

    def __init__(self, cookie_file=None, insecure=False, log_http_detail=False):
        """
        :param cookie_file: File name to use as on-disk cookie jar.
        :type  cookie_file: str

        :param insecure: If set to True, don't validate server certificate.
        :type  insecure: bool

        :param log_http_detail: If set to True, increases HTTP level logging.
        :type  log_http_detail: bool
        """
        super(SessionStore, self).__init__()
        self._init_logging(log_http_detail)
        self._init_security(insecure)
        self._init_cookie_jar(cookie_file)

        self.lock = Lock()
        self.too_many_requests_count = 0

    def _init_logging(self, http_detail=False):
        self.log = get_logger('%s.%s' % (__name__, self.__class__.__name__))
        init_http_logging(self.log.getEffectiveLevel(), http_detail)

    def _init_security(self, insecure):
        self.verify = (insecure is False)
        if insecure:
            try:
                requests.packages.urllib3.disable_warnings(
                    requests.packages.urllib3.exceptions.InsecureRequestWarning)
            except:
                import urllib3
                urllib3.disable_warnings(
                    urllib3.exceptions.InsecureRequestWarning)

    def _init_cookie_jar(self, cookie_file):
        if cookie_file is None:
            cookie_file = DEFAULT_COOKIE_FILE
        cookie_dir = os.path.dirname(cookie_file)
        self.cookies = MozillaCookieJar(cookie_file)
        # Create cookie store directory, if it doesn't exist.
        if not os.path.isdir(cookie_dir):
            os.mkdir(cookie_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        # Load existing cookies, if exist.
        if os.path.isfile(cookie_file):
            self.cookies.load(ignore_discard=True)
            self.cookies.clear_expired_cookies()

    @staticmethod
    def _update_request_params(kwargs):
        if kwargs.get('stream', False):
            kwargs['headers'] = set_stream_header(kwargs.get('headers', {}))

        if 'timeout' in kwargs:
            if isinstance(kwargs['timeout'], float):
                # Only 'read timeout' is set; prepend 'connect timeout'.
                kwargs['timeout'] = (HTTP_CONNECT_TIMEOUT, kwargs['timeout'])
        else:
            kwargs['timeout'] = HTTP_TIMEOUTS

    def request(self, method, url, **kwargs):
        """Generic HTTP request expecting HTTP verb and URL.

        :param method: HTTP verb
        :type  method: str

        :param url: HTTP URL
        :type  url: str

        :param kwargs: see requests.Session.request()
        :type  kwargs: dict

        :keyword stream: Enable SSE. Default: disabled
        :type    stream: bool

        :keyword timeout: read timeout, or connect timeout and read timeout
        :type    timeout: float or (float, float)

        :keyword retry: Whether to retry or not the requests. Default: False
        :type    retry: bool

        :return: requests.models.Response or generator for SSE events

        Returns
        - HTTP response
        or if `stream` was provided in kwargs and set to True,
        - streamed SSE response. To get the events, one should iterate over
        `response.events()` consuming `data` field of each event. When all of
        the required data is obtained, `close()` the stream explicitly.
        Example:

        for i, e in enumerate(response.events()):
            print json.loads(e.data)
            if i >= 4:
                stream.close()
                break
        """
        self._update_request_params(kwargs)

        try:
            retry = kwargs.pop('retry')
        except KeyError:
            retry = False
        retry_until = 60 * 60 * 24 * 7  # 7 days in seconds
        max_wait_time = 60 * 15  # 15 minutes in seconds
        retry_count = 0
        first_request_time = time.time()

        while True:
            try:
                response = self._request(method, url, kwargs)
                response = self._handle_response(response, kwargs)
                with self.lock:
                    if self.too_many_requests_count > 0:
                        self.too_many_requests_count -= 1
                return response

            except requests.exceptions.Timeout as ex:
                # Retry w/o timeout on HTTP connect and read timeouts.
                # requests.exceptions.Timeout - server might be overloaded.
                self.log.warning('HTTP request timed out.')
                if retry:
                    kwargs['timeout'] = (kwargs['timeout'][0] * 2,
                                         kwargs['timeout'][1] * 2)
                    sleep = 1.
                else:
                    self.log.error('Retry disabled. HTTP call error: %s', ex)
                    raise

            except (TooManyRequestsError,
                    ServiceUnavailableError) as ex:
                # Retry w/o timeout on the server side errors that highly
                # likely to go away soon.
                # TooManyRequestsError - server side back-pressure
                # ServiceUnavailableError - server in maintenance mode
                if retry:
                    s = abs(float(self.too_many_requests_count) / 10.0 * 290 +
                            10)
                    sleep = min(s, 300)
                    with self.lock:
                        if self.too_many_requests_count < 11:
                            self.too_many_requests_count += 1
                else:
                    self.log.warning('Retry disabled. HTTP call error: %s', ex)
                    raise

            except (socket.error,
                    requests.exceptions.ConnectionError,
                    ServerError,
                    BadStatusLine,
                    HTTPException) as ex:
                # Retry w/ timeout.
                # socket.error - host is down
                # requests.exceptions.ConnectionError - API gateway is not
                #                                       running
                # ServerError - application behind API gateway is not running
                if retry:
                    if (time.time() - first_request_time) >= retry_until:
                        self.log.error('Timed out retrying. HTTP call error: '
                                       '%s', ex)
                        raise
                    sleep = min(float(retry_count) * 10.0, float(max_wait_time))
                    retry_count += 1
                else:
                    self.log.error('Retry disabled. HTTP call error: %s', ex)
                    raise

            except requests.exceptions.InvalidSchema as ex:
                raise ClientError("Malformed URL: %s" % ex)

            except Exception as ex:
                raise Exception('Failed {} on {} with: {}'.format(method, url,
                                                                  ex))

            sleep += (random() * sleep * 0.2) - (sleep * 0.1)
            self.log.warning('Error: %s. Retrying in %s seconds.' % (ex, sleep))
            time.sleep(sleep)
            self.log.warning('Retrying...')

    def _request(self, method, url, kwargs):
        """Returns successful or unsuccessful response.  Throws on timeouts
        or any unexpected failures.

        :param method: HTTP verb
        :type  method: str
        :param url: SlipStream resource URL
        :type  url: str
        :param kwargs: see `requests.sessions.Session.request()`
        :return: `requests.models.Response`
        """
        try:
            return super(SessionStore, self).request(method, url, **kwargs)
        except BadStatusLine:
            raise BadStatusLine("Error: BadStatusLine contacting: %s" % url)

    def _handle_response(self, response, kwargs):
        """Returns handled response

        :param response:
        :param kwargs:
        :return:
        """
        self._log_response(response)

        status = response.status_code

        if 100 <= status < 300:
            if not self.verify and response.cookies:
                self._unsecure_cookie(response)
            self.cookies.save(ignore_discard=True)
            if kwargs.get('stream', False):
                return sseclient.SSEClient(response)
            else:
                return response
        elif 300 <= status < 400:
            self._handle3xx(response)
        elif 400 <= status < 500:
            self._handle4xx(response)
        elif 500 <= status < 600:
            self._handle5xx(response)
        else:
            raise ServerError('Unknown HTTP return code: %s' % status)

    @staticmethod
    def _handle3xx(resp):
        raise Exception("Redirect should have been handled by HTTP library."
                        "%s: %s" % (resp.status_code, resp.reason))

    @staticmethod
    def _handle4xx(resp):
        status = resp.status_code
        if status == CONFLICT_ERROR:
            raise AbortException(resp.text)
        if status == PRECONDITION_FAILED_ERROR:
            raise NotYetSetException(resp.text)
        if status == EXPECTATION_FAILED_ERROR:
            raise TerminalStateException(resp.text)
        if status == TOO_MANY_REQUESTS_ERROR:
            raise TooManyRequestsError("Too Many Requests")

        if status == NOT_FOUND_ERROR:
            clientEx = NotFoundError(resp.reason)
        else:
            url = resp.url
            method = resp.request.method
            detail = resp.text
            detail = detail and detail or (
                "%s (%d)" % (resp.reason, status))
            msg = "Failed calling method %s on url %s, with reason: %s" % (
                method, url, detail)
            clientEx = ClientError(msg)

        clientEx.code = status
        raise clientEx

    @staticmethod
    def _handle5xx(resp):
        if resp.status_code == SERVICE_UNAVAILABLE_ERROR:
            raise ServiceUnavailableError("SlipStream is in maintenance.")
        else:
            url = resp.url
            method = resp.request.method
            raise ServerError(
                "Failed calling method %s on url %s, with reason: %d: %s"
                % (method, url, resp.status_code, resp.reason))

    def _unsecure_cookie(self, response):
        url = urlparse(response.url)
        if url.scheme == 'http':
            for cookie in response.cookies:
                cookie.secure = False
                self.cookies.set_cookie_if_ok(cookie, MockRequest(response.request))

    def clear(self, domain):
        """Clear cookies for the specified domain."""
        try:
            self.cookies.clear(domain)
            self.cookies.save()
        except KeyError:
            pass

    def _log_response(self, resp, max_characters=1000):
        if is_streamed_response(resp):
            msg = 'Received streaming response.'
        else:
            msg = 'Received response: %s\nWith content: %s' % (resp, resp.text)
        if len(msg) > max_characters:
            msg = '%s\n                         %s' % (
                msg[:max_characters], '::::: Content truncated :::::')
        self.log.debug(msg)