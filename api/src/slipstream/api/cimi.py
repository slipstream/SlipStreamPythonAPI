"""
Implementation of CIMI protocol from https://www.dmtf.org/standards/cloud.
"""

import re
from threading import Lock
from requests.exceptions import HTTPError
from .exceptions import SlipStreamError
from .defaults import DEFAULT_ENDPOINT
from . import models
from .log import get_logger

CIMI_PARAMETERS_NAME = ['first', 'last', 'filter', 'select', 'expand',
                        'orderby']

CLOUD_ENTRY_POINT_RESOURCE = 'api/cloud-entry-point'
SESSION_TEMPLATE_RESOURCE_TYPE = 'sessionTemplates'


class CIMI(object):
    """Implementation of CIMI protocol."""

    def __init__(self, session, endpoint=DEFAULT_ENDPOINT):
        """
        :param http_session: Object providing request() method for making HTTP
                             requests.
        :type  http_session: requests.Session like object
        :param endpoint: SlipStream base URL.
        """
        self.session = session
        self.endpoint = endpoint
        self._cep = None
        self._base_uri = None
        self.log = get_logger('%s.%s' % (__name__, self.__class__.__name__))
        self.lock = Lock()

    def _get_cloud_entry_point(self):
        url = '{}/{}'.format(self.endpoint, CLOUD_ENTRY_POINT_RESOURCE)
        self.log.debug('Get cloud entry point on: {}'.format(url))
        return self._get(url)

    @property
    def cloud_entry_point(self):
        """Cloud entry point.
        :return: Cloud entry point as map.
        :rtype: dict
        """
        if self._cep is None:
            self._cep = self._get_cloud_entry_point()
        return self._cep

    @property
    def base_uri(self):
        return self.cloud_entry_point['baseURI']

    @staticmethod
    def _split_params(params):
        cimi_params = {}
        other_params = {}
        for key, value in params.items():
            if key in CIMI_PARAMETERS_NAME:
                cimi_params['$'+key] = value
            else:
                other_params[key] = value
        return cimi_params, other_params

    @staticmethod
    def get_operation_href(cimi_resource, operation):
        operation_href = cimi_resource.operations_by_name.get(operation, {}).\
            get('href')

        if not operation_href:
            raise KeyError("Operation '{}' not found on resource {}.".format(
                operation, cimi_resource.id))

        return operation_href

    def get_collection_href(self, resource_type):
        """Obtain entry point for a resource collection of the type
        `resource_type`.
        """
        return self.cloud_entry_point[resource_type]['href']

    def _to_url(self, url_or_id):
        if re.match('((http://)|(https://).*)', url_or_id):
            return url_or_id
        else:
            return '{}/{}'.format(self.base_uri.rstrip('/'),
                                  url_or_id.lstrip('/'))

    def _get_uri(self, resource_id=None, resource_type=None):
        if resource_id is None and resource_type is None:
            raise TypeError("You have to specify 'resource_uri' or "
                            "'resource_type'.")

        if resource_id is not None and resource_type is not None:
            raise TypeError("You can only specify 'resource_uri' or "
                            "'resource_type', not both.")

        if resource_type is not None:
            resource_id = self.get_collection_href(resource_type)
            if resource_id is None:
                raise KeyError("Resource of type '%s' not found." %
                               resource_type)

        return resource_id

    def _request(self, method, url_or_id, params=None, json=None, data=None,
                 stream=False, retry=False):
        url = self._to_url(url_or_id)
        with self.lock:
            response = self.session.request(
                method, url,
                headers={'Accept': 'application/json'},
                params=params,
                json=json,
                data=data,
                stream=stream,
                retry=retry)

        if stream:
            return response
        else:
            self._check_response_status(response)
            return response.json()

    @staticmethod
    def _check_response_status(response):
        try:
            response.raise_for_status()
        except HTTPError as e:
            message = 'Unknown error'
            try:
                json_msg = e.response.json()
                message = json_msg.get('message')
                if message is None:
                    error = json_msg.get('error')
                    message = error.get('code') + ' - ' + error.get('reason')
            except:
                try:
                    message = e.response.text
                except:
                    message = str(e)
            raise SlipStreamError(message, response)

    def _get(self, resource_id=None, resource_type=None, params=None,
             stream=False, retry=False):
        uri = self._get_uri(resource_id, resource_type)
        return self._request('GET', uri, params=params, stream=stream,
                             retry=retry)

    def _post(self, resource_id=None, resource_type=None, params=None, json=None,
              data=None, retry=False):
        uri = self._get_uri(resource_id, resource_type)
        return self._request('POST', uri, params=params, json=json, data=data,
                             retry=retry)

    def _put(self, resource_id=None, resource_type=None, params=None, json=None,
             data=None, stream=False, retry=False):
        uri = self._get_uri(resource_id, resource_type)
        return self._request('PUT', uri, params=params, json=json, data=data,
                             stream=stream, retry=retry)

    def _delete(self, resource_id=None, retry=False):
        return self._request('DELETE', resource_id, retry=retry)

    def get(self, resource_id, stream=False, retry=False):
        """ Retrieve a CIMI resource by it's resource id

        :param   resource_id: The id of the resource to retrieve
        :type    resource_id: str

        :param   retry: Retry HTTP request on errors
        :type    retry: bool

        :param   stream: Requests SSE
        :type    stream: bool

        :return: CimiResource object corresponding to the resource
        """
        return self._get(resource_id=resource_id, stream=stream, retry=retry)

    def edit(self, resource_id, data, retry=False):
        """ Edit a CIMI resource by it's resource id

        :param   resource_id: The id of the resource to edit
        :type    resource_id: str

        :param   data: The data to serialize into JSON
        :type    data: dict

        :param   retry: Retry HTTP request on errors
        :type    retry: bool

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        resource = models.CimiResource(self.get(resource_id=resource_id))
        operation_href = self.get_operation_href(resource, 'edit')
        return self._put(resource_id=operation_href, json=data, retry=retry)

    def delete(self, resource_id, retry=False):
        """ Delete a CIMI resource by it's resource id

        :param   resource_id: The id of the resource to delete
        :type    resource_id: str

        :param   retry: Retry HTTP request on errors
        :type    retry: bool

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        resource = models.CimiResource(self.get(resource_id=resource_id))
        operation_href = self.get_operation_href(resource, 'delete')
        return self._delete(resource_id=operation_href, retry=retry)

    def add(self, resource_type, data, retry=False):
        """ Add a CIMI resource to the specified resource_type (Collection)

        :param   resource_type: Type of the resource (Collection name)
        :type    resource_type: str

        :param   data: The data to serialize into JSON
        :type    data: dict

        :param   retry: Retry HTTP request on errors
        :type    retry: bool

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        collection = models.CimiCollection(self.search(
            resource_type=resource_type, last=0), resource_type)
        operation_href = self.get_operation_href(collection, 'add')
        return self._post(resource_id=operation_href, json=data, retry=retry)

    def search(self, resource_type, retry=False, stream=False, **kwargs):
        """ Search for CIMI resources of the given type (Collection).

        :param   resource_type: Type of the resource (Collection name)
        :type    resource_type: str

        :param   retry: Retry HTTP request on errors
        :type    retry: bool

        :param   stream: Requests SSE
        :type    stream: bool

        :keyword first: Start from the 'first' element (1-based)
        :type    first: int

        :keyword last: Stop at the 'last' element (1-based)
        :type    last: int

        :keyword filter: CIMI filter
        :type    filter: str

        :keyword select: Select attributes to return. (resourceURI always
                         returned)
        :type    select: str or list of str

        :keyword expand: Expand linked resources (not implemented yet)
        :type    expand: str or list of str

        :keyword orderby: Sort by the specified attribute
        :type    orderby: str or list of str

        :return: Dictionary with the list of found resources
        :rtype:  dict
        """
        cimi_params, query_params = self._split_params(kwargs)
        return self._put(resource_type=resource_type, params=query_params,
                         data=cimi_params, stream=stream, retry=retry)

    def login(self, login_params):
        """Uses given login_params to log into the SlipStream server. The
        login_params must be a map containing an "href" element giving the id of
        the sessionTemplate resource and any other attributes required for the
        login method. E.g.:

        {"href" : "session-template/internal",
         "username" : "username",
         "password" : "password"}
         or
        {"href" : "session-template/api-key",
         "key" : "key",
         "secret" : "secret"}

        Returns server response as dict. Successful responses will contain a
        `status` code of 201 and the `resource-id` of the created session.

        :param   login_params: {"href": "session-template/...", <creds>}
        :type    login_params: dict
        :return: Server response.
        :rtype:  dict
        """
        return self._post(resource_type='sessions',
                          json={'sessionTemplate': login_params})

    def login_internal(self, username, password):
        """Wrapper around login() for internal authentication.  For details
        see login().

        :param username: User login name
        :param password: User password
        :return:  see login()
        """
        if not self.is_authenticated():
            self.login({'href': self.href_login_internal(),
                        'username': username,
                        'password': password})

    def login_apikey(self, key, secret):
        """Wrapper around login() for API key based authentication.  For details
        see login().

        :param key: API key
        :param secret: API secret
        :return: see login()
        """
        return self.login({'href': self.href_login_apikey(),
                           'key': key,
                           'secret': secret})

    def logout(self):
        id = self.current_session()
        if id is not None:
            return self.delete(id)

    def current_session(self):
        """
        :return: str (session id) or None (if session is not available)
        """
        resource_type = 'sessions'
        session = models.CimiCollection(self.search(resource_type),
                                        resource_type)
        if session and session.count > 0:
            return session.sessions[0].get('id')
        else:
            return None

    def is_authenticated(self):
        return self.current_session() is not None

    def href_login_internal(self):
        return '{}/{}'.format(
            self.get_collection_href(SESSION_TEMPLATE_RESOURCE_TYPE),
            'internal')

    def href_login_apikey(self):
        return '{}/{}'.format(
            self.get_collection_href(SESSION_TEMPLATE_RESOURCE_TYPE),
            'api-key')

