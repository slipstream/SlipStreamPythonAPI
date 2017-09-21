from .log import get_logger
from .http import http_proto_re


class Module(object):
    def __init__(self, cimi, uri=None):
        """

        :param cimi: CIMI cimi
        :param uri:
        """
        self.cimi = cimi
        self.uri = uri
        self.log = get_logger()

    def get(self, url_or_uri=None):
        url = self._to_url(url_or_uri or self.uri)
        response = self.cimi.session.get(url,
                                         headers={'Accept': 'application/xml',
                                                  'Content-Type': 'application/xml'})
        self.cimi._check_response_status(response)
        return response.text

    def edit(self, url_or_uri, module):
        url = self._to_url(url_or_uri or self.uri)
        response = self.cimi.session.put(url, data=module,
                                         headers={'Accept': 'application/xml',
                                                  'Content-Type': 'application/xml'})
        self.cimi._check_response_status(response)
        return response

    def create(self, url_or_uri, module):
        url = self._to_url(url_or_uri or self.uri)
        response = self.cimi.session.post(url, data=module,
                                          headers={'Accept': 'application/xml',
                                                   'Content-Type': 'application/xml'})
        self.cimi._check_response_status(response)
        return response

    def delete(self, url_or_uri=None):
        url = self._to_url(url_or_uri or self.uri)
        response = self.cimi.session.delete(url,
                                            headers={'Accept': 'application/xml'})
        self.cimi._check_response_status(response)
        return response

    def _to_url(self, url_or_uri):
        if not url_or_uri:
            raise Exception('URI is not provided.')
        elif http_proto_re.match(url_or_uri):
            return url_or_uri
        else:
            m = ''
            if not url_or_uri.startswith('/module'):
                m = '/module'
            return '{}{}/{}'.format(self.cimi.endpoint, m,
                                    url_or_uri.lstrip('/'))
