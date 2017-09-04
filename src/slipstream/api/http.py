"""
HTTP session via cookie jar implemented over `requests`.
"""

import os
import re
import stat
import requests
from requests.cookies import MockRequest
from six.moves.urllib.parse import urlparse
from six.moves.http_cookiejar import MozillaCookieJar
import sseclient
from .defaults import DEFAULT_COOKIE_FILE

HEADER_SSE = 'text/event-stream'


def has_key(_dict, key):
    """Case insensitive search for a key in a map.
    """
    return any(map(lambda k: re.match('%s$' % key, k, re.I), _dict.keys()))


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


class SessionStore(requests.Session):
    """A ``requests.Session`` subclass implementing a file-based session store.
    """

    def __init__(self, cookie_file=None, insecure=False):
        super(SessionStore, self).__init__()
        self._init_security(insecure)
        self._init_cookie_jar(cookie_file)

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

    def request(self, method, url, **kwargs):
        """Generic HTTP request expecting HTTP verb and URL.

        :param method: str HTTP verb
        :param url: str HTTP URL
        :param kwargs: see requests.Session
        :return: requests.models.Response or generator for SSE events

        Returns
        - HTTP response
        or if `stream` was provided in kwargs and set to True,
        - streamed SSE response. To get the events, one should iterate over
        `stream.events()` consuming `data` field of each event. When all of
        the required data is obtained, `close()` the stream explicitly.
        Example:

        for i, e in enumerate(stream.events()):
            print json.loads(e.data)
            if i >= 4:
                stream.close()
                break

        TODO:
         - handle connection retries via retry option. See HttpClient for
         current implementation.

        """
        stream = kwargs.get('stream', False)
        if stream:
            kwargs['headers'] = set_stream_header(kwargs.get('headers', {}))
        response = super(SessionStore, self).request(method, url, **kwargs)
        if stream:
            return sseclient.SSEClient(response)
        if not self.verify and response.cookies:
            self._unsecure_cookie(url, response)
        self.cookies.save(ignore_discard=True)
        return response

    def _unsecure_cookie(self, url_str, response):
        url = urlparse(url_str)
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
