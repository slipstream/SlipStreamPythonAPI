"""
Implementation of CIMI protocol from https://www.dmtf.org/standards/cloud.
"""

from requests.exceptions import HTTPError
from .exceptions import SlipStreamError
from .defaults import DEFAULT_ENDPOINT
from . import models
from .log import get_logger

CIMI_PARAMETERS_NAME = ['first', 'last', 'filter', 'select', 'expand',
                        'orderby']


class CIMI(object):
    """Implementation of CIMI protocol."""

    def __init__(self, http_session, endpoint=DEFAULT_ENDPOINT):
        """
        :param http_session: Object providing request() method for making HTTP
                             requests.
        :type  http_session: requests.Session like object
        :param endpoint: SlipStream base URL.
        """
        self.http_session = http_session
        self.endpoint = endpoint
        self._cep = None
        self.log = get_logger('%s.%s' % (__name__, self.__class__.__name__))

    def _get_cloud_entry_point(self):
        cep_json = self._get('cloud-entry-point')
        return models.CloudEntryPoint(cep_json)

    @property
    def cloud_entry_point(self):
        """Cloud entry point.
        :return: models.CloudEntryPoint
        """
        if self._cep is None:
            self._cep = self._get_cloud_entry_point()
        return self._cep

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
    def _find_operation_href(cimi_resource, operation):
        operation_href = cimi_resource.operations_by_name.get(operation, {}).\
            get('href')

        if not operation_href:
            raise KeyError("Operation '{}' not found.".format(operation))

        return operation_href

    def _get_uri(self, resource_id=None, resource_type=None):
        if resource_id is None and resource_type is None:
            raise TypeError("You have to specify 'resource_uri' or "
                            "'resource_type'.")

        if resource_id is not None and resource_type is not None:
            raise TypeError("You can only specify 'resource_uri' or "
                            "'resource_type', not both.")

        if resource_type is not None:
            resource_id = self.cloud_entry_point.entry_points.get(resource_type)
            if resource_id is None:
                raise KeyError("Resource type '%s' not found." % resource_type)

        return resource_id

    def _request(self, method, resource, params=None, json=None, data=None,
                 stream=False, retry=False):
        response = self.http_session.request(
            method, '{}/{}/{}'.format(self.endpoint, 'api', resource),
            headers={'Accept': 'application/json'},
            params=params,
            json=json,
            data=data,
            stream=stream,
            retry=retry)

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

        :param   stream: Requests SSE
        :type    stream: bool

        :return: CimiResource object corresponding to the resource
        """
        resp_json = self._get(resource_id=resource_id, stream=stream,
                              retry=retry)
        if stream:
            return resp_json
        else:
            return models.CimiResource(resp_json)

    def edit(self, resource_id, data, retry=False):
        """ Edit a CIMI resource by it's resource id

        :param   resource_id: The id of the resource to edit
        :type    resource_id: str

        :param   data: The data to serialize into JSON
        :type    data: dict

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        resource = self.get(resource_id=resource_id)
        operation_href = self._find_operation_href(resource, 'edit')
        return models.CimiResponse(self._put(resource_id=operation_href,
                                             json=data, retry=retry))

    def delete(self, resource_id, retry=False):
        """ Delete a CIMI resource by it's resource id

        :param   resource_id: The id of the resource to delete
        :type    resource_id: str

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        resource = self.get(resource_id=resource_id)
        operation_href = self._find_operation_href(resource, 'delete')
        return models.CimiResponse(self._delete(resource_id=operation_href,
                                                retry=retry))

    # TODO: SSE
    def add(self, resource_type, data, retry=False):
        """ Add a CIMI resource to the specified resource_type (Collection)

        :param   resource_type: Type of the resource (Collection name)
        :type    resource_type: str

        :param   data: The data to serialize into JSON
        :type    data: dict

        :return: CimiResponse object which should contain the attributes
                 'status', 'resource-id' and 'message'
        :rtype:  CimiResponse
        """
        collection = self.search(resource_type=resource_type, last=0)
        operation_href = self._find_operation_href(collection, 'add')
        return models.CimiResponse(self._post(resource_id=operation_href,
                                              json=data, retry=retry))

    # TODO: SSE
    def search(self, resource_type, retry=False, **kwargs):
        """ Search for CIMI resources of the given type (Collection).

        :param   resource_type: Type of the resource (Collection name)
        :type    resource_type: str

        :param   retry: Retry HTTP calls
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

        :return: CimiCollection object with the list of found resources
                 available as a generator with the method 'resources()' or
                 with the attribute 'resources_list'.
        :rtype:  CimiCollection
        """
        stream = kwargs.get('stream', False)
        cimi_params, query_params = self._split_params(kwargs)
        resp_json = self._put(resource_type=resource_type, params=query_params,
                              data=cimi_params, stream=stream, retry=retry)
        if stream:
            return resp_json
        else:
            return models.CimiCollection(resp_json, resource_type)

    def login(self, login_params):
        """Uses given login_params to log into the SlipStream server. The
        login_params must be a map containing an "href" element giving the id of
        the sessionTemplate resource and any other attributes required for the
        login method. E.g.:
        {"href" : "session-template/internal",
         "username" : "username",
         "password" : "password"}
        Returns models.CimiResponse. Successful responses will contain a status
        code of 201 and the resource-id of the session.

        :param   login_params: {"href": "session-template/...", <creds>}
        :return: models.CimiResponse
        """
        return models.CimiResponse(
            self._post(resource_type='sessions',
                       json={'sessionTemplate': login_params}))

    def login_internal(self, username, password):
        return self.login({'href': self.href_login_internal(),
                           'username': username,
                           'password': password})

    def login_apikey(self, key, secret):
        return self.login({'href': self.href_login_apikey(),
                           'key': key,
                           'secret': secret})

    def logout(self):
        id = self.current_session()
        if id is not None:
            return self.delete(id)

    def current_session(self):
        """
        :return: str - session id
        """
        session = self.search('sessions')
        if session and session.count > 0:
            id = session.sessions[0].get('id')
            return id

    def is_authenticated(self):
        return self.current_session() is not None

    def href_login_internal(self):
        return self.cloud_entry_point.entry_points['sessionTemplates'] + \
               '/internal'

    def href_login_apikey(self):
        return self.cloud_entry_point.entry_points['sessionTemplates'] + \
               '/api-key'
