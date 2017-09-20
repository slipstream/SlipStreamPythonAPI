import re

from .module import Module
from .deployment import Deployment, DEPLOYMENT_RESOURCE_TYPE


def decamelcase(s):
    # FIXME: lookahead doesn't work
    if s:
        return '_'.join(map(lambda x: x.lower(), re.split('(?=[A-Z])', s)))


def strip_unvanted_attrs(d):
    for k in ["id", "resourceURI", "acl", "operations", "created", "updated",
              "name", "description"]:
        try:
            d.pop(k)
        except:
            pass
    return d


template_resource_tag = 'deploymentTemplate'
templates_resource_type = 'deploymentTemplates'
template_resource_name = 'DeploymentTemplate'
standard_template_name = 'standard'


class Application(Module):

    def __init__(self, cimi, uri=None):
        """

        :param cimi: CIMI cimi
        :param uri:
        """
        super(Application, self).__init__(cimi, uri)

    def deploy(self, uri=None):
        """
        :param module_uri: Application URI
        :return: Provisioned application
        :rtype: slipstream.api.deployment.Deployment
        """
        uri = uri or self.uri
        dpl_req = self._get_deployment_request(uri)
        if not dpl_req:
            raise Exception('Failed to deploy {}. No deployment '
                            'template found.'.format(uri))
        res = self.cimi.add(DEPLOYMENT_RESOURCE_TYPE, dpl_req)
        if 'resource-id' in res:
            dpl = Deployment(self.cimi, res['resource-id'])
            dpl.start()
            return dpl
        else:
            raise Exception('Failed to deploy {}.'.format(uri))

    def _get_deployment_request(self, uri):
        flt = "method='{}'".format(standard_template_name)
        templates = self.cimi.search(templates_resource_type, filter=flt)
        if templates['count'] > 0:
            dpl_tmpl = templates[templates_resource_type][0]
            href = dpl_tmpl.get('id')
            return {template_resource_tag: {'href': href, 'module': uri}}
        else:
            self.log.warning('No templates for {} with {}'.format(
                templates_resource_type, flt))
            return {}
