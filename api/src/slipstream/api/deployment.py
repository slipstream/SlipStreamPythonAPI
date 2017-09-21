"""
Deployment resource.
"""

import re
from .models import CimiResource

DEPLOYMENT_RESOURCE_TYPE = 'deployments'
DEPLOYMENT_TEMPLATE_RESOURCE_TYPE = 'deploymentTemplates'

PARAMETER_SEPAR = '_'
PARAMETER_RESOURCE_TYPE = 'deploymentParameters'

deployment_op_delete_name = 'delete'
deployment_op_start_name = 'http://schemas.dmtf.org/cimi/2/action/start'
deployment_op_terminate_name = 'http://schemas.dmtf.org/cimi/2/action/terminate'

DEPLOYMENT_STATES = ('Initializing',
                     'Provisioning',
                     'Executing',
                     'SendingReports',
                     'Ready',
                     'Finalizing',
                     'Done',
                     'Cancelled',
                     'Aborted')

FINAL_STATES = ('Done',
                'Cancelled',
                'Aborted')


def deployment_url_to_uuid(run_url):
    return run_url.rsplit('/', 1)[-1]


def deployment_states_after(state):
    return DEPLOYMENT_STATES[DEPLOYMENT_STATES.index(state) + 1:]


def is_global_ns(comp):
    return comp and (comp == ND.GLOBAL_NS or
                     comp.startswith(ND.GLOBAL_NS +
                                     ND.NODE_PROPERTY_SEPARATOR))


def is_machine(comp):
    return comp == ND.MACHINE_NAME


class Deployment(object):
    def __init__(self, cimi, resource_id):
        """
        :param cimi: authenticated client implementing CIMI over HTTP CRUD.
        :type  cimi: slipstream.api.cimi.CIMI
        :param resource_id: Deployment URI in the form:
                            <href of DEPLOYMENT_RESOURCE_TYPE>/<uuid>
        :type  resource_id: str
        """
        self.cimi = cimi
        self.resource_id = self._ensure_resource_id(resource_id)

    def _ensure_resource_id(self, id):
        href = self.deployment_href()
        if not id.startswith(href):
            return '/'.join([href, id.strip('/')])
        else:
            return id

    def _dpl_uuid(self):
        return self.resource_id.split('/')[-1]

    @property
    def url(self):
        return self.cimi.base_uri + self.resource_id

    def _resource_href(self, rtype):
        return self.cimi.get_resource_href(rtype)

    def param_href(self):
        return self._resource_href(PARAMETER_RESOURCE_TYPE)

    def deployment_href(self):
        return self._resource_href(DEPLOYMENT_RESOURCE_TYPE)

    def to_param_id(self, comp, index, name):
        param = PARAMETER_SEPAR.join(
            [self._dpl_uuid(), comp, str(index), name])
        return '/'.join([self.param_href(), param])

    def to_param_id_global(self, name):
        param = PARAMETER_SEPAR.join([self._dpl_uuid(), name])
        return '/'.join([self.param_href(), param])

    def to_param_id_machine(self, name):
        return self.to_param_id(ND.MACHINE_NAME, 1, name)

    def state(self, retry=False, stream=False):
        return self.get_deployment_parameter_global('state', retry=retry,
                                                    stream=stream)

    def is_aborted(self, retry=False):
        p = self.get_deployment_parameter_global('abort', retry=retry)
        return '' == p.get('value')

    def start(self, dpl_params=None):
        start_href = self._get_op_href(deployment_op_start_name)
        return self.cimi._post(start_href, json=dpl_params)

    def _get_op_href(self, op_name):
        # TODO: to parent class
        resource = CimiResource(self.cimi.get(self.resource_id))
        return self.cimi.get_operation_href(resource, op_name)

    def get_deployment_parameter(self, comp, name, index=None, retry=False,
                                 stream=False):
        """When `index` is provided, returns value (as `models.CimiResource`)
        of the requested deployment parameter `name` of the specified `component`.
        Otherwise, returns all currently active `component`s (as
        `models.CimiCollection`).

        Set `stream` to `True` to active SSE.

        :param   comp: Component name
        :param   name: Parameter name
        :param   index: Index of component instance
        :param   stream: Use SSE
        :param   retry: Retry or not on errors
        :return: deployment parameter(s) or generator of them, if `stream` True
        :rtype:  dict, list of dicts or generator of dicts
        """
        if index:
            # node.id:name
            param_id = self.to_param_id(comp, index, name)
            return self.cimi.get(param_id, stream=stream, retry=retry)
        elif is_global_ns(comp):
            # ss:name
            param_id = self.to_param_id_global(name)
            return self.cimi.get(param_id, stream=stream, retry=retry)
        elif is_machine(comp):
            # machine:name
            param_id = self.to_param_id_machine(name)
            return self.cimi.get(param_id, stream=stream, retry=retry)
        elif comp and name:
            # Value of parameter `name` from all `component` instances.
            # node.<active ids>:name
            # FIXME: add "ACTIVE component instance" filter
            _filter = 'node-name="{}" and ' \
                      'name="{}" and ' \
                      'deployment/href="{}"'.format(comp, name,
                                                    self.resource_id)
            res = self.cimi.search(PARAMETER_RESOURCE_TYPE, filter=_filter,
                                   retry=retry, stream=stream)
            # FIXME: take into account paging.
            if stream:
                return res
            else:
                return res.get('deploymentParameters')
        else:
            raise Exception("Don't know now to get parameter: component '{}', "
                            "index '{}', name '{}'".format(comp or '',
                                                           index or '',
                                                           name or ''))

    def get_deployment_parameter_global(self, name, retry=False, stream=False):
        """Returns global parameter.

        :param name: Deployment parameter name from the global namespace
        :param retry:
        :param stream:
        :return:
        """
        return self.get_deployment_parameter(ND.GLOBAL_NS, name,
                                             retry=retry, stream=stream)

    def get_deployment_parameter_machine(self, name, retry=False, stream=False):
        """Returns machine parameter.

        :param name: Deployment parameter name of single component deployment.
        :param retry:
        :param stream:
        :return:
        """
        return self.get_deployment_parameter(ND.MACHINE_NAME, name,
                                             retry=retry, stream=stream)

    def set_deployment_parameter(self, comp, name, index=None, value='',
                                 retry=False):
        """Sets `value` on deployment parameter `name` of the `component`
        instance with `index`.

        :param   comp: Component name
        :param   index: Index of component instance
        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        if index:
            # node.id:name
            param_id = self.to_param_id(comp, index, name)
            return self.cimi.edit(param_id, {'value': value}, retry=retry)
        elif is_global_ns(comp):
            # ss:name
            self.set_deployment_parameter_global(name, value, retry=retry)
        elif is_machine(comp):
            # machine:name
            self.set_deployment_parameter_machine(name, value, retry=retry)
        else:
            raise Exception("Don't know now to set parameter: component '{}', "
                            "index '{}', name '{}'".format(comp or '',
                                                           index or '',
                                                           name or ''))

    def set_deployment_parameter_global(self, name, value, retry=False):
        """Sets `value` on global deployment parameter `name` in ss namespace.

        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        param_id = self.to_param_id_global(name)
        return self.cimi.edit(param_id, {'value': value}, retry=retry)

    def set_deployment_parameter_machine(self, name, value, retry=False):
        """Sets `value` on machine deployment parameter `name`.

        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        param_id = self.to_param_id_machine(name)
        return self.cimi.edit(param_id, {'value': value}, retry=retry)

    def terminate(self):
        """Terminates the deployment by stopping and releasing all the cloud
        resources.
        :return:
        """
        op_href = self._get_op_href(deployment_op_terminate_name)
        return self.cimi._post(op_href)

    def delete(self):
        """Deletes the deployment and all the associated resources on
        SlipStream side.
        :return:
        """
        op_href = self._get_op_href(deployment_op_delete_name)
        return self.cimi.delete(op_href)

    def get_deployment(self):
        """
        TODO: get deployment and then get all its deployment parameters.
        :return:
        """
        return self.cimi.get(self.resource_id)


RUN_CATEGORY_IMAGE = 'Image'
RUN_CATEGORY_DEPLOYMENT = 'Deployment'
KEY_RUN_CATEGORY = 'run_category'


class NodeDecorator(object):
    # Execution instance property namespace and separator
    GLOBAL_NS = 'ss'
    NODE_PROPERTY_SEPARATOR = ':'
    GLOBAL_NS_PREFIX = GLOBAL_NS + NODE_PROPERTY_SEPARATOR

    ABORT_KEY = 'abort'

    # Node multiplicity index separator - e.g. <nodename>.<index>:<prop>
    NODE_MULTIPLICITY_SEPARATOR = '.'
    nodeMultiplicityStartIndex = '1'

    # Counter names
    initCounterName = GLOBAL_NS_PREFIX + 'initCounter'
    finalizeCounterName = GLOBAL_NS_PREFIX + 'finalizeCounter'
    terminateCounterName = GLOBAL_NS_PREFIX + 'terminateCounter'

    # Orchestrator name
    orchestratorName = 'orchestrator'
    ORCHESTRATOR_NODENAME_RE = re.compile(
        '^' + orchestratorName + '(-\w[-\w]*)?$')

    # Name given to the machine being built for node state
    MACHINE_NAME = 'machine'
    defaultMachineNamePrefix = MACHINE_NAME + NODE_PROPERTY_SEPARATOR

    # List of reserved and special node names
    reservedNodeNames = [GLOBAL_NS, orchestratorName, MACHINE_NAME]

    NODE_NAME_KEY = 'nodename'
    NODE_INSTANCE_NAME_KEY = 'node_instance_name'

    NODE_PRERECIPE = 'prerecipe'
    NODE_RECIPE = 'recipe'
    NODE_PACKAGES = 'packages'

    DEFAULT_SCRIPT_NAME = 'unnamed'

    IS_ORCHESTRATOR_KEY = 'is.orchestrator'

    # State names
    STATE_KEY = 'state'
    COMPLETE_KEY = 'complete'
    STATECUSTOM_KEY = 'statecustom'

    RECOVERY_MODE_KEY = 'recovery.mode'

    RUN_BUILD_RECIPES_KEY = 'run-build-recipes'
    PLATFORM_KEY = 'platform'
    LOGIN_USER_KEY = 'loginUser'
    LOGIN_PASS_KEY = 'login.password'
    BUILD_STATE_KEY = 'build.state'
    SCALE_STATE_KEY = 'scale.state'
    SCALE_IAAS_DONE = 'scale.iaas.done'
    SCALE_IAAS_DONE_SUCCESS = 'true'
    PRE_SCALE_DONE = 'pre.scale.done'
    PRE_SCALE_DONE_SUCCESS = 'true'
    SCALE_DISK_ATTACH_SIZE = 'disk.attach.size'
    SCALE_DISK_ATTACHED_DEVICE = 'disk.attached.device'
    SCALE_DISK_DETACH_DEVICE = 'disk.detach.device'
    INSTANCEID_KEY = 'instanceid'
    CLOUDSERVICE_KEY = 'cloudservice'
    SECURITY_GROUPS_KEY = 'security.groups'
    MAX_PROVISIONING_FAILURES_KEY = 'max-provisioning-failures'
    NATIVE_CONTEXTUALIZATION_KEY = 'native-contextualization'

    SECURITY_GROUP_ALLOW_ALL_NAME = 'slipstream_managed'
    SECURITY_GROUP_ALLOW_ALL_DESCRIPTION = 'Security group created by SlipStream which allows all kind of traffic.'

    urlIgnoreAbortAttributeFragment = '?ignoreabort=true'

    SLIPSTREAM_DIID_ENV_NAME = 'SLIPSTREAM_DIID'

    IMAGE = RUN_CATEGORY_IMAGE
    DEPLOYMENT = RUN_CATEGORY_DEPLOYMENT

    RUN_TYPE_ORCHESTRATION = 'Orchestration'
    RUN_TYPE_MACHINE = 'Machine'
    RUN_TYPE_RUN = 'Run'

    MODULE_RESOURCE_URI = 'moduleResourceUri'

    @staticmethod
    def is_orchestrator_name(name):
        return True if NodeDecorator.ORCHESTRATOR_NODENAME_RE.match(
            name) else False


ND = NodeDecorator

