"""
Deployment resource.
"""

RESOURCE_TYPE = 'deployment'
PARAMETER_SEPAR = '_'
PARAMETER_RESOURCE = 'deployment-parameter'


def to_param_id(deployment_id, component, index, name):
    param = PARAMETER_SEPAR.join([deployment_id, component, str(index), name])
    return '/'.join([PARAMETER_RESOURCE, param])


class Deployment(object):

    def __init__(self, cimi, id):
        """
        :param cimi: authenticated client implementing CIMI over HTTP CRUD.
        """
        self.cimi = cimi
        self.id = id

    def state(self, stream=False):
        res = self.cimi.get(PARAMETER_RESOURCE + '/' + self.id +
                            PARAMETER_SEPAR + 'state',
                            stream=stream)
        if stream:
            return res
        else:
            return res.get('value')

    def get_deployment_parameter(self, component, index, name, stream=False):
        """When `index` is provided, returns value (as `models.CimiResource`)
        of the requested deployment parameter `name` of the specified `component`.
        Otherwise, returns all currently active `component`s (as
        `models.CimiCollection`).

        Set `stream` to `True` to active SSE.

        :param   component: Component name
        :param   index: Index of component instance
        :param   name: Parameter name
        :param   stream: Use SSE
        :return: deployment parameter value or generator, if `stream` is True
        :rtype:  str or generator
        """
        if index:
            param_id = to_param_id(self.id, component, index, name)
            res = self.cimi.get(param_id, stream=stream)
            if stream:
                return res
            else:
                return res.get('value')

    def get_deployment_parameters(self, component, name, retry=False,
                                  stream=False):
        # FIXME: add "ACTIVE node instance" filter
        _filter = 'node-name="{}" and ' \
                  'name="{}" and ' \
                  'deployment-href="{}/{}"'.format(component, name,
                                                   RESOURCE_TYPE, self.id)
        return self.cimi.search(RESOURCE_TYPE, filter=_filter,
                                retry=retry, stream=stream)

    def set_deployment_parameter(self, component, index, name, value):
        """Sets `value` on deployment parameter `name` of the `component`
        instance with `index`.

        :param   component: Component name
        :param   index: Index of component instance
        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        param_id = to_param_id(self.id, component, index, name)
        return self.cimi.edit(param_id, {'value': value})

    def get_deployment(self):
        """
        TODO: get deployment and then get all its deployment parameters.
        :return:
        """
        pass
