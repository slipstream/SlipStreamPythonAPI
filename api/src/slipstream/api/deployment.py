"""
Deployment resource.
"""

RESOURCE_TYPE = 'deployments'
PARAMETER_SEPAR = '_'
PARAMETER_RESOURCE = 'deployment-parameter'


def to_param_id(deployment_id, component, index, name):
    param = PARAMETER_SEPAR.join([deployment_id, component, str(index), name])
    return '/'.join([PARAMETER_RESOURCE, param])


class Deployment(object):

    def __init__(self, client, deployment_id):
        """
        :param client: authenticated client implementing CIMI over HTTP CRUD.
        """
        self.client = client
        self.deployment_id = deployment_id

    def get_deployment_parameter(self, component, name, index=None, stream=False):
        """When `index` is provided, returns value (as `models.CimiResource`)
        of the requested deployment parameter `name` of the specified `component`.
        Otherwise, returns all currently active `component`s (as
        `models.CimiCollection`).

        Set `stream` to `True` to active SSE.

        :param   component: Component name
        :param   name: Parameter name
        :param   index: Index of component instance
        :param   stream: Use SSE
        :return: `models.CimiResource` or `models.CimiCollection`, or generator
                 of `models.CimiResource`
        """
        if index:
            param_id = to_param_id(self.deployment_id, component, index, name)
            return self.client.get(param_id, stream=stream)
        else:
            return self.client.search(RESOURCE_TYPE, stream=stream)

    def set_deployment_parameter(self, component, index, name, value):
        """Sets `value` on deployment parameter `name` of the `component`
        instance with `index`.

        :param   component: Component name
        :param   index: Index of component instance
        :param   name: Parameter name
        :param   value: Value to set
        :return:
        """
        param_id = to_param_id(self.deployment_id, component, index, name)
        return self.client.edit(param_id, value)

    def get_deployment(self):
        """
        TODO: get deployment and then get all its deployment parameters.
        :return:
        """
        pass
