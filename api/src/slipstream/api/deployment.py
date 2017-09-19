"""
Deployment resource.
"""

import re

DEPLOYMENT_RESOURCE_TYPE = 'deployments'
TEMPLATE_RESOURCE_TYPE = 'deploymentTemplates'

PARAMETER_SEPAR = '_'
PARAMETER_RESOURCE_TYPE = 'deploymentParameters'

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


def is_global_ns(name):
    return name and (name == NodeDecorator.GLOBAL_NS or
                     name.startswith(NodeDecorator.GLOBAL_NS +
                                     NodeDecorator.NODE_PROPERTY_SEPARATOR))


class Deployment(object):

    def __init__(self, cimi, id):
        """
        :param cimi: authenticated client implementing CIMI over HTTP CRUD.
        """
        self.cimi = cimi
        self.id = id

    def _resource_href(self, rtype):
        return self.cimi.get_resource_href(rtype)

    def param_href(self):
        return self._resource_href(PARAMETER_RESOURCE_TYPE)

    def deployment_href(self):
        return self._resource_href(DEPLOYMENT_RESOURCE_TYPE)

    def to_param_id(self, deployment_id, component, index, name):
        param = PARAMETER_SEPAR.join([deployment_id, component, str(index), name])
        return '/'.join([self.param_href(), param])

    def to_global_param_id(self, deployment_id, name):
        param = PARAMETER_SEPAR.join([deployment_id, name])
        return '/'.join([self.param_href(), param])

    def to_deployment_id(self, id):
        return '/'.join([self.deployment_href(), id])

    def state(self, retry=False, stream=False):
        return self.get_deployment_parameter(NodeDecorator.GLOBAL_NS,
                                             'state', retry=retry,
                                             stream=stream)

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
            param_id = self.to_param_id(self.id, comp, index, name)
            return self.cimi.get(param_id, stream=stream, retry=retry)
        elif is_global_ns(comp):
            # ss:name
            param_id = self.to_global_param_id(self.id, name)
            return self.cimi.get(param_id, stream=stream, retry=retry)
        elif comp and name:
            # Value of parameter `name` from all `component` instances.
            # node.<active ids>:name
            # FIXME: add "ACTIVE component instance" filter
            rtype = self.cimi.get_resource_href(DEPLOYMENT_RESOURCE_TYPE)
            _filter = 'node-name="{}" and ' \
                      'name="{}" and ' \
                      'deployment-href="{}/{}"'.format(comp, name,
                                                       rtype, self.id)
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

    def set_deployment_parameter(self, component, index, name, value):
        """Sets `value` on deployment parameter `name` of the `component`
        instance with `index`.

        :param   component: Component name
        :param   index: Index of component instance
        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        param_id = self.to_param_id(self.id, component, index, name)
        return self.cimi.edit(param_id, {'value': value})

    def get_deployment(self):
        """
        TODO: get deployment and then get all its deployment parameters.
        :return:
        """
        pass


RUN_CATEGORY_IMAGE = 'Image'
RUN_CATEGORY_DEPLOYMENT = 'Deployment'
KEY_RUN_CATEGORY = 'run_category'


class NodeDecorator(object):
    # Execution instance property namespace and separator
    GLOBAL_NS = 'ss'
    NODE_PROPERTY_SEPARATOR = ':'
    globalNamespacePrefix = GLOBAL_NS + NODE_PROPERTY_SEPARATOR

    ABORT_KEY = 'abort'

    # Node multiplicity index separator - e.g. <nodename>.<index>:<prop>
    NODE_MULTIPLICITY_SEPARATOR = '.'
    nodeMultiplicityStartIndex = '1'

    # Counter names
    initCounterName = globalNamespacePrefix + 'initCounter'
    finalizeCounterName = globalNamespacePrefix + 'finalizeCounter'
    terminateCounterName = globalNamespacePrefix + 'terminateCounter'

    # Orchestrator name
    orchestratorName = 'orchestrator'
    ORCHESTRATOR_NODENAME_RE = re.compile('^' + orchestratorName + '(-\w[-\w]*)?$')

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
        return True if NodeDecorator.ORCHESTRATOR_NODENAME_RE.match(name) else False
