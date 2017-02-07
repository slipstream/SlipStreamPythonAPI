from __future__ import absolute_import

import os
import six
import stat
import uuid
import logging

import requests
from six import string_types, integer_types
from six.moves.urllib.parse import urlparse
from six.moves.http_cookiejar import MozillaCookieJar

from . import models

try:
    from defusedxml import cElementTree as etree
except ImportError:
    from defusedxml import ElementTree as etree

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

DEFAULT_ENDPOINT = 'https://nuv.la'
DEFAULT_COOKIE_FILE = os.path.expanduser('~/.slipstream/cookies.txt')

def _mod_url(path):
    parts = path.strip('/').split('/')
    if parts[0] == 'module':
        del parts[0]
    return '/module/' + '/'.join(parts)


def _mod(path, with_version=True):
    parts = path.split('/')
    if with_version:
        return '/'.join(parts[1:])
    else:
        return '/'.join(parts[1:-1])


def get_module_type(category):
    mapping = {'image': 'component',
               'deployment': 'application'}
    return mapping.get(category.lower(), category.lower())


def ElementTree__iter(root):
    return getattr(root, 'iter',  # Python 2.7 and above
                   root.getiterator)  # Python 2.6 compatibility


class SlipStreamError(Exception):

    def __init__(self, reason):
        super(SlipStreamError, self).__init__(reason)
        self.reason = reason


class SessionStore(requests.Session):
    """A ``requests.Session`` subclass implementing a file-based session store."""

    def __init__(self, cookie_file=None):
        super(SessionStore, self).__init__()
        if cookie_file is None:
            cookie_file = DEFAULT_COOKIE_FILE
        cookie_dir = os.path.dirname(cookie_file)
        self.cookies = MozillaCookieJar(cookie_file)
        # Create the $HOME/.slipstream dir if it doesn't exist
        if not os.path.isdir(cookie_dir):
            os.mkdir(cookie_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        # Load existing cookies if the cookies.txt exists
        if os.path.isfile(cookie_file):
            self.cookies.load(ignore_discard=True)
            self.cookies.clear_expired_cookies()

    def request(self, *args, **kwargs):
        response = super(SessionStore, self).request(*args, **kwargs)
        self.cookies.save(ignore_discard=True)
        return response

    def clear(self, domain):
        """Clear cookies for the specified domain."""
        try:
            self.cookies.clear(domain)
            self.cookies.save()
        except KeyError:
            pass


class Api(object):
    """ This class is a Python wrapper&helper of the native SlipStream REST API"""

    GLOBAL_PARAMETERS = ['bypass-ssh-check', 'refqname', 'keep-running', 'tags', 'mutable', 'type']
    KEEP_RUNNING_VALUES = ['always', 'never', 'on-success', 'on-error']

    def __init__(self, endpoint=None, cookie_file=None, insecure=False):
        self.endpoint = DEFAULT_ENDPOINT if endpoint is None else endpoint
        self.session = SessionStore(cookie_file)
        self.session.verify = (insecure == False)
        self.session.headers.update({'Accept': 'application/xml'})
        if insecure:
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning)
        self.username = None

    def login(self, username, password):
        """

        :param username: 
        :param password: 

        """
        self.username = username

        response = self.session.post('%s/auth/login' % self.endpoint, data={
            'username': username,
            'password': password
        })
        response.raise_for_status()

    def logout(self):
        """ """
        response = self.session.get('%s/logout' % self.endpoint)
        response.raise_for_status()
        url = urlparse(self.endpoint)
        self.session.clear(url.netloc)

    def _xml_get(self, url, **params):
        response = self.session.get('%s%s' % (self.endpoint, url),
                                    headers={'Accept': 'application/xml'},
                                    params=params)
        response.raise_for_status()

        parser = etree.DefusedXMLParser(encoding='utf-8')
        parser.feed(response.text.encode('utf-8'))
        return parser.close()

    def _xml_put(self, url, data):
        return self.session.put('%s%s' % (self.endpoint, url),
                                headers={'Accept': 'application/xml',
                                         'Content-Type': 'application/xml'},
                                data=data)

    def _json_get(self, url, **params):
        response = self.session.get('%s%s' % (self.endpoint, url),
                                    headers={'Accept': 'application/json'},
                                    params=params)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _add_to_dict_if_not_none(d, key, value):
        if key is not None and value is not None:
            d[key] = value

    @staticmethod
    def _dict_values_to_string(d):
        return {k: v if isinstance(v, six.string_types) else str(v) for k,v in six.iteritems(d)}

    def create_user(self, username, password, email, first_name, last_name,
                    organization=None, roles=None, privileged=False,
                    default_cloud=None, default_keep_running='never',
                    ssh_public_keys=None, log_verbosity=1, execution_timeout=30,
                    usage_email='never', cloud_parameters=None):
        """
        Create a new user into SlipStream.

        :param username: The user's username (need to be unique)
        :type username: str
        :param password: The user's password
        :type password: str
        :param email: The user's email address
        :type email: str
        :param first_name: The user's first name
        :type first_name: str
        :param last_name: The user's last name
        :type last_name: str
        :param organization: The user's organization/company
        :type organization: str|None
        :param roles: The user's roles
        :type roles: list
        :param privileged: true to create a privileged user, false otherwise
        :type privileged: bool
        :param default_cloud: The user's default Cloud
        :type default_cloud: str|None
        :param default_keep_running: The user's default setting for keep-running.
        :type default_keep_running: 'always' or 'never' or 'on-success' or 'on-error'
        :param ssh_public_keys: The SSH public keys to inject into deployed instances.
                                One key per line.
        :type ssh_public_keys: str|None
        :param log_verbosity: The verbosity level of the logging inside instances.
                              0: Actions, 1: Steps, 2: Details, 3: Debugging
        :type log_verbosity: 0 or 1 or 2 or 3
        :param execution_timeout: If a deployment stays in a transitionnal state
                                  for more than this value (in minutes) it will
                                  be forcefully terminated.
        :type execution_timeout: int
        :param usage_email: Set it to 'daily' if you want to receive daily email
                            with a summary of your Cloud usage of the previous day.
        :type usage_email: 'never' or 'daily'
        :param cloud_parameters: To add Cloud specific parameters (like credentials).
                                 A dict with the cloud name as the key and a dict of parameter as the value.
        :type cloud_parameters: dict|None

        """
        attrib = dict(name=username, password=password, email=email,
                      firstName=first_name, lastName=last_name,
                      issuper=privileged,
                      state='ACTIVE', resourceUri='user/{}'.format(username))
        self._add_to_dict_if_not_none(attrib, 'organization', organization)
        self._add_to_dict_if_not_none(attrib, 'roles', roles)
        _attrib = self._dict_values_to_string(attrib)

        parameters = {}
        if cloud_parameters is not None:
            for cloud, params in six.iteritems(cloud_parameters):
                for name, value in six.iteritems(params):
                    parameters['{}.{}'.format(cloud, name)] = value

        self._add_to_dict_if_not_none(parameters, 'General.default.cloud.service', default_cloud)
        self._add_to_dict_if_not_none(parameters, 'General.keep-running', default_keep_running)
        self._add_to_dict_if_not_none(parameters, 'General.Verbosity Level', log_verbosity)
        self._add_to_dict_if_not_none(parameters, 'General.Timeout', execution_timeout)
        self._add_to_dict_if_not_none(parameters, 'General.mail-usage', usage_email)
        self._add_to_dict_if_not_none(parameters, 'General.ssh.public.key', ssh_public_keys)

        _parameters = self._dict_values_to_string(parameters)

        user_xml = ET.Element('user', **_attrib)

        params_xml = ET.SubElement(user_xml, 'parameters')
        for name, value in six.iteritems(_parameters):
            category = name.split('.', 1)[0]
            entry_xml = ET.SubElement(params_xml, 'entry')
            ET.SubElement(entry_xml, 'string').text = name
            param_xml = ET.SubElement(entry_xml, 'parameter', name=name, category=category)
            ET.SubElement(param_xml, 'value').text = value

        response = self._xml_put('/user/{}'.format(username), etree.tostring(user_xml, 'UTF-8'))

        if not (200 <= response.status_code < 300):
            reason = ''
            try:
                reason = etree.fromstring(response.text).get('detail')
            except:
                pass
            else:
                raise SlipStreamError(reason)
        response.raise_for_status()

        return True

    def get_user(self, username=None):
        """
        Get informations for a given user, if permitted
        :param username: The username of the user.
                         Default to the user logged in if not provided or None.
        :type path: str|None
        """
        if not username:
            username = self.username

        try:
            root = self._xml_get('/user/%s' % username)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for user: {0}.")
            raise

        general_params = {}
        with_username = set()
        with_password = set()

        for p in root.findall('parameters/entry/parameter'):
            name = p.get('name', '')
            value = p.findtext('value', '')
            category = p.get('category', '')

            if (name.endswith('.username') or name.endswith('.access.id')) and value:
                with_username.add(category)
            elif (name.endswith('.password') or name.endswith('.secret.key')) and value:
                with_password.add(category)
            elif category == 'General':
                general_params[name] = value

        configured_clouds = with_username & with_password

        user = models.User(
            username=root.get('name'),
            cyclone_login=root.get('cycloneLogin'),
            email=root.get('email'),
            first_name=root.get('firstName'),
            last_name=root.get('lastName'),
            organization=root.get('organization'),
            configured_clouds=configured_clouds,
            default_cloud=general_params.get('General.default.cloud.service'),
            ssh_public_keys=general_params.get('General.ssh.public.key', '').splitlines(),
            keep_running=general_params.get('General.keep-running'),
            timeout=general_params.get('General.Timeout'),
            privileged=root.get('issuper').lower() == "true",
        )
        return user

    def list_applications(self):
        """
        List apps in the appstore
        """
        root = self._xml_get('/appstore')
        for elem in ElementTree__iter(root)('item'):
            yield models.App(name=elem.get('name'),
                             type=get_module_type(elem.get('category')),
                             version=int(elem.get('version')),
                             path=_mod(elem.get('resourceUri'),
                                      with_version=False))

    def get_element(self, path):
        """
        Get details about a project, a component or an application

        :param path: The path of an element (project/component/application)
        :type path: str

        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise

        module = models.Module(name=root.get('shortName'),
                               type=get_module_type(root.get('category')),
                               created=root.get('creation'),
                               modified=root.get('lastModified'),
                               description=root.get('description'),
                               version=int(root.get('version')),
                               path=_mod('%s/%s' % (root.get('parentUri').strip('/'),
                                                   root.get('shortName'))))
        return module

    def get_application_nodes(self, path):
        """
        Get nodes of an application
        :param path: The path of an application
        :type path: str
        """
        url = _mod_url(path)
        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
            raise
        for node in root.findall("nodes/entry/node"):
            yield models.Node(path=_mod(node.get("imageUri")),
                              name=node.get('name'),
                              cloud=node.get('cloudService'),
                              multiplicity=node.get('multiplicity'),
                              max_provisioning_failures=node.get('maxProvisioningFailures'),
                              network=node.get('network'),
                              cpu=node.get('cpu'),
                              ram=node.get('ram'),
                              disk=node.get('disk'),
                              extra_disk_volatile=node.get('extraDiskVolatile'),
                              )

    def list_project_content(self, path=None, recurse=False):
        """
        List the content of a project

        :param path: The path of a project. If None, list the root project.
        :type path: str
        :param recurse: Get project content recursively
        :type recurse: bool

        """
        logger.debug("Starting with path: {0}".format(path))
        # Path normalization
        if not path:
            url = '/module'
        else:
            url = _mod_url(path)
        logger.debug("Using normalized URL: {0}".format(url))

        try:
            root = self._xml_get(url)
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                logger.debug("Access denied for path: {0}. Skipping.".format(path))
                return
            raise

        for elem in ElementTree__iter(root)('item'):
            # Compute module path
            if elem.get('resourceUri'):
                app_path = elem.get('resourceUri')
            else:
                app_path = "%s/%s" % (root.get('parentUri').strip('/'),
                                      '/'.join([root.get('shortName'),
                                                elem.get('name'),
                                                elem.get('version')]))

            module_type = get_module_type(elem.get('category'))
            logger.debug("Found '{0}' with path: {1}".format(module_type, app_path))
            app = models.App(name=elem.get('name'),
                             type=module_type,
                             version=int(elem.get('version')),
                             path=_mod(app_path, with_version=False))
            yield app
            if app.type == 'project' and recurse:
                logger.debug("Recursing into path: {0}".format(app_path))
                for app in self.list_project_content(app_path, recurse):
                    yield app

    def list_deployments(self, inactive=False):
        """
        List deployments

        :param inactive: Include inactive deployments. Default to False

        """
        root = self._xml_get('/run', activeOnly=(not inactive))
        for elem in ElementTree__iter(root)('item'):
            yield models.Deployment(id=uuid.UUID(elem.get('uuid')),
                                    module=_mod(elem.get('moduleResourceUri')),
                                    status=elem.get('status').lower(),
                                    started_at=elem.get('startTime'),
                                    last_state_change=elem.get('lastStateChangeTime'),
                                    cloud=elem.get('cloudServiceNames'),
                                    username=elem.get('username'),
                                    abort=elem.get('abort'),
                                    service_url=elem.get('serviceUrl'),
                                    scalable=elem.get('mutable'),
                                    )

    def get_deployment(self, deployment_id):
        """
        Get a deployment

        :param deployment_id: The deployment UUID of the deployment to get
        :type deployment_id: str or UUID

        """
        root = self._xml_get('/run/' + str(deployment_id))

        abort = root.findtext('runtimeParameters/entry/runtimeParameter[@key="ss:abort"]')
        service_url = root.findtext('runtimeParameters/entry/runtimeParameter[@key="ss:url.service"]')

        return models.Deployment(id=uuid.UUID(root.get('uuid')),
                                 module=_mod(root.get('moduleResourceUri')),
                                 status=root.get('state').lower(),
                                 started_at=root.get('startTime'),
                                 last_state_change=root.get('lastStateChangeTime'),
                                 clouds=root.get('cloudServiceNames','').split(','),
                                 username=root.get('user'),
                                 abort=abort,
                                 service_url=service_url,
                                 scalable=root.get('mutable'),
                                 )

    def list_virtualmachines(self, deployment_id=None, offset=0, limit=20):
        """
        List virtual machines

        :param deployment_id: Retrieve only virtual machines about the specified run_id. Default to None
        :type deployment_id: str or UUID
        :param offset: Retrieve virtual machines starting by the offset<exp>th</exp> one. Default to 0
        :param limit: Retrieve at most 'limit' virtual machines. Default to 20

        """
        if deployment_id is not None:
            _deployment_id = str(deployment_id)

        root = self._xml_get('/vms', offset=offset, limit=limit, runUuid=_deployment_id)
        for elem in ElementTree__iter(root)('vm'):
            run_id_str = elem.get('runUuid')
            run_id = uuid.UUID(run_id_str) if run_id_str is not None else None
            yield models.VirtualMachine(id=elem.get('instanceId'),
                                        cloud=elem.get('cloud'),
                                        status=elem.get('state').lower(),
                                        deployment_id=run_id,
                                        deployment_owner=elem.get('runOwner'),
                                        ip=elem.get('ip'),
                                        cpu=elem.get('cpu'),
                                        ram=elem.get('ram'),
                                        disk=elem.get('disk'),
                                        instance_type=elem.get('instanceType'),
                                        is_usable=elem.get('isUsable'))

    def build_component(self, path, cloud=None):
        """

        :param path: The path to a component
        :type path: str
        :param cloud: The Cloud on which to build the component. If None, the user default Cloud will be used.
        :type cloud: str

        """
        response = self.session.post(self.endpoint + '/run', data={
            'type': 'Machine',
            'refqname': path,
            'parameter--cloudservice': cloud or 'default',
        })
        response.raise_for_status()
        run_id = response.headers['location'].split('/')[-1]
        return uuid.UUID(run_id)

    def deploy(self, path, cloud=None, parameters=None, tags=None, keep_running=None, scalable=False, multiplicity=None,
               tolerate_failures=None, check_ssh_key=False, raw_params=None):
        """
        Run a component or an application

        :param path: The path of the component/application to deploy
        :type path: str
        :param cloud: A string or a dict to specify on which Cloud(s) to deploy the component/application.
                      To deploy a component simply specify the Cloud name as a string.
                      To deploy a deployment specify a dict with the nodenames as keys and Cloud names as values.
                      If not specified the user default cloud will be used.
        :type cloud: str or dict
        :param parameters: A dict of parameters to redefine for this deployment.
                           To redefine a parameter of a node use "<nodename>" as keys and dict of parameters as values.
                           To redefine a parameter of a component or a global parameter use "<parametername>" as the key.
        :type parameters: dict
        :param tags: List of tags that can be used to identify or annotate a deployment
        :type tags: str or list
        :param keep_running: [Only apply to applications] Define when to terminate or not a deployment when it reach the
                             'Ready' state. Possibles values: 'always', 'never', 'on-success', 'on-error'.
                             If scalable is set to True, this value is ignored and it will behave as if it was set to 'always'.
                             If not specified the user default will be used.
        :type keep_running: 'always' or 'never' or 'on-success' or 'on-error'
        :param scalable: [Only apply to applications] True to start a scalable deployment. Default: False
        :type scalable: bool
        :param multiplicity: [Only apply to applications] A dict to specify how many instances to start per node.
                             Nodenames as keys and number of instances to start as values.
        :type multiplicity: dict
        :param tolerate_failures: [Only apply to applications] A dict to specify how many failures to tolerate per node.
                                  Nodenames as keys and number of failure to tolerate as values.
        :type tolerate_failures: dict
        :param check_ssh_key: Set it to True if you want the SlipStream server to check if you have a public ssh key
                              defined in your user profile. Useful if you want to ensure you will have access to VMs.
        :type check_ssh_key: bool
        :param raw_params: This allows you to pass parameters directly in the request to the SlipStream server.
                           Keys must be formatted in the format understood by the SlipStream server.
        :type raw_params: dict

        :return: The deployment UUID of the newly created deployment
        :rtype: uuid.UUID
        """

        _raw_params = dict() if raw_params is None else raw_params
        _raw_params.update(self._convert_parameters_to_raw_params(parameters))
        _raw_params.update(self._convert_clouds_to_raw_params(cloud))
        _raw_params.update(self._convert_multiplicity_to_raw_params(multiplicity))
        _raw_params.update(self._convert_tolerate_failures_to_raw_params(tolerate_failures))
        _raw_params['refqname'] = path

        if tags:
            _raw_params['tags'] = tags if isinstance(tags, six.string_types) else ','.join(tags)

        if keep_running:
            if keep_running not in self.KEEP_RUNNING_VALUES:
                raise ValueError('"keep_running" should be one of {}, not "{}"'.format(self.KEEP_RUNNING_VALUES,
                                                                                     keep_running))
            _raw_params['keep-running'] = keep_running

        if scalable:
            _raw_params['mutable'] = 'on'

        if not check_ssh_key:
            _raw_params['bypass-ssh-check'] = 'true'

        response = self.session.post(self.endpoint + '/run', data=_raw_params)

        if response.status_code == 409:
            reason = etree.fromstring(response.text).get('detail')
            raise SlipStreamError(reason)

        response.raise_for_status()
        deployment_id = response.headers['location'].split('/')[-1]
        return uuid.UUID(deployment_id)

    def terminate(self, deployment_id):
        """
        Terminate a deployment

        :param deployment_id: The UUID of the deployment to terminate
        :type deployment_id: str or uuid.UUID

        """
        response = self.session.delete('%s/run/%s' % (self.endpoint, deployment_id))
        response.raise_for_status()
        return True

    def add_node_instances(self, deployment_id, node_name, quantity=None):
        """
        Add new instance(s) of a deployment's node (horizontal scale up).
        
        Warning: The targeted deployment has to be "scalable".

        :param deployment_id: The deployment UUID of the deployment on which to add new instances of a node.
        :type deployment_id: str|UUID
        :param node_name: Name of the node where to add instances.
        :type node_name: str
        :param quantity: Amount of node instances to add. If not provided it's server dependent (usually add one instance)
        :type quantity: int

        :return: The list of new node instance names.
        :rtype: list

        """
        url = '%s/run/%s/%s' % (self.endpoint, str(deployment_id), str(node_name))
        data = {"n": quantity} if quantity else None
        
        response = self.session.post(url, data=data)

        response.raise_for_status()

        return response.text.split(",")

    def remove_node_instance(self, deployment_id, node_name, ids):
        """
        Remove a list of node instances from a deployment.
        
        Warning: The targeted deployment has to be "scalable".

        :param deployment_id: The deployment UUID of the deployment on which to remove instances of a node.
        :type deployment_id: str|UUID
        :param node_name: Name of the node where to remove instances.
        :type node_name: str
        :param ids: List of node instance ids to remove. Ids can also be provided as a CSV list.
        :type ids: list|str

        :return: True on success
        :rtype: bool

        """
        url = '%s/run/%s/%s' % (self.endpoint, str(deployment_id), str(node_name))

        response = self.session.delete(url, data={"ids": ",".join(str(id_) for id_ in ids)})

        response.raise_for_status()

        return response.status_code == 204

    def usage(self):
        """
        Get current usage and quota by cloud service.
        """
        root = self._xml_get('/dashboard')
        for elem in ElementTree__iter(root)('cloudUsage'):
            yield models.Usage(cloud=elem.get('cloud'),
                               quota=int(elem.get('vmQuota')),
                               run_usage=int(elem.get('userRunUsage')),
                               vm_usage=int(elem.get('userVmUsage')),
                               inactive_vm_usage=int(elem.get('userInactiveVmUsage')),
                               others_vm_usage=int(elem.get('othersVmUsage')),
                               pending_vm_usage=int(elem.get('pendingVmUsage')),
                               unknown_vm_usage=int(elem.get('unknownVmUsage')))

    def publish(self, path):
        """
        Publish a component or an application to the appstore

        :param path: The path to a component or an application

        """
        response = self.session.put('%s%s/publish' % (self.endpoint,
                                                      _mod_url(path)))
        response.raise_for_status()
        return True

    def unpublish(self, path):
        """
        Unpublish a component or an application from the appstore

        :param path: The path to a component or an application

        """
        response = self.session.delete('%s%s/publish' % (self.endpoint,
                                                         _mod_url(path)))
        response.raise_for_status()
        return True

    def delete_element(self, path):
        """
        Delete a project, a component or an application

        :param path: The path to a component or an application

        """
        response = self.session.delete('%s%s' % (self.endpoint, _mod_url(path)))

        response.raise_for_status()
        return True

    @staticmethod
    def _check_type(obj_name, obj, allowed_types):
        if not isinstance(obj, allowed_types):
            raise ValueError('Invalid type "{}" for "{}"'.format(type(obj), obj_name))

    @classmethod
    def _convert_clouds_to_raw_params(cls, clouds):
        return cls._convert_per_node_parameter_to_raw_params('cloudservice', clouds, allowed_types=string_types)

    @classmethod
    def _convert_multiplicity_to_raw_params(cls, multiplicity):
        return cls._convert_per_node_parameter_to_raw_params('multiplicity', multiplicity,
                                                             allowed_types=(integer_types, string_types))

    @classmethod
    def _convert_tolerate_failures_to_raw_params(cls, tolerate_failures):
        return cls._convert_per_node_parameter_to_raw_params('max-provisioning-failures', tolerate_failures,
                                                             allowed_types=(integer_types, string_types))

    @classmethod
    def _convert_per_node_parameter_to_raw_params(cls, parameter_name, parameters, allowed_types=(string_types, int),
                                                  allow_no_node=True):
        raw_params = dict()

        if parameters is None:
            return raw_params

        if isinstance(parameters, dict):
            for key, value in parameters.items():
                cls._check_type('{}:{}'.format(key, parameter_name), value, allowed_types)
                raw_params['parameter--node--{}--{}'.format(key, parameter_name)] = value
        elif allow_no_node:
            cls._check_type(parameter_name, parameters, allowed_types)
            raw_params['parameter--{}'.format(parameter_name)] = parameters
        else:
            cls._check_type(parameter_name, parameters, dict)

        return raw_params

    @classmethod
    def _convert_parameters_to_raw_params(cls, parameters):
        raw_params = dict()

        if parameters is None:
            return raw_params

        for key, value in parameters.items():
            if isinstance(value, dict):
                # Redefine node parameters
                for parameter_name, parameter_value in value.items():
                    raw_params['parameter--node--{}--{}'.format(key, parameter_name)] = parameter_value
            else:
                if key in cls.GLOBAL_PARAMETERS:
                    # Redefine a global parameter
                    raw_params[key] = value
                else:
                    # Redefine a component parameter
                    raw_params['parameter--{}'.format(key)] = value

        return raw_params



