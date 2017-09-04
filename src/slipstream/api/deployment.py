"""
Deployment resource.
"""

PARAMETER_SEPAR = '%'
PARAMETER_RESOURCE = 'run-parameter'


def to_param_id(deployment_id, component, index, name):
    return '/'.join([PARAMETER_RESOURCE,
                     PARAMETER_SEPAR.join([deployment_id, component, str(index),
                                           name])])


class Deployment(object):

    def __init__(self, client, deployment_id):
        """
        :param client: authenticated client implementing CIMI over HTTP CRUD.
        """
        self.client = client
        self.deployment_id = deployment_id

    def get_deployment_parameter(self, component, name, index=None, stream=False):
        if index:
            param_id = to_param_id(self.deployment_id, component, index, name)
            return self.client.get(param_id, stream=stream)
        else:
            return self.client.search(param_id, stream=stream)

    def set_deployment_parameter(self, component, index, name, value):
        param_id = to_param_id(self.deployment_id, component, index, name)
        self.client.edit(param_id, value)
