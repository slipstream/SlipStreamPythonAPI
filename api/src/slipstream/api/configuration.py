from pprint import pprint as pp

from .log import Logger

RESOURCE_ID = 'configuration/slipstream'

SERVER_CONFIG_FILE_EXT = '.conf'
SERVER_CONFIGURATION_BASICS_CATEGORY = 'SlipStream_Basics'
SERVER_CONFIGURATION_DEFAULT_CATEGORIES = ['SlipStream_Support',
                                           SERVER_CONFIGURATION_BASICS_CATEGORY,
                                           'SlipStream_Advanced']
SERVER_CONFIGURATION_CONNECTOR_CLASSES_KEY = 'cloud.connector.class'


def get_cloud_connector_classes(config):
    """
    :param config: representation of the configuration
    :type config: dict
    :rtype: dict
    """
    cloud_connector_classes = {}
    for p in config.get(SERVER_CONFIGURATION_BASICS_CATEGORY, []):
        if len(p) == 2:
            k, v = p
            if k == SERVER_CONFIGURATION_CONNECTOR_CLASSES_KEY:
                cloud_connector_classes = _connector_classes_str_to_dict(v)
                break
    return cloud_connector_classes


def _connector_classes_str_to_dict(classes_conf_str):
    """
    Input: 'foo:bar, baz'
    Result: {'foo': 'bar', 'baz': 'baz'}
    """
    if len(classes_conf_str) == 0:
        return {}
    classes_conf_dict = {}
    for cc in classes_conf_str.split(','):
        cc_t = cc.strip().split(':')
        if len(cc_t) == 1:
            classes_conf_dict[cc_t[0]] = cc_t[0]
        else:
            classes_conf_dict[cc_t[0]] = cc_t[1]
    return classes_conf_dict


class Configuration(Logger):

    def __init__(self, cimi):
        super(Configuration, self).__init__()
        self.cimi = cimi

    def get(self):
        return self.cimi.get(RESOURCE_ID)

    def get_xml(self):
        """
        FIXME: Remove later. For ss-config-dump.py
        """
        url = '{}/{}'.format(self.cimi.endpoint.rstrip('/'), 'configuration')
        response = self.cimi.session.get(url,
                                         headers={'Accept': 'application/xml',
                                                  'Content-Type': 'application/xml'})
        self.cimi._check_response_status(response)
        return response.text

    def set(self, conf):
        return self.cimi.edit(RESOURCE_ID, conf)

    def edit(self, conf):
        """Edits resource by setting merged version.

        :param conf: configuration parameters to update
        :type  conf: dict
        :return:
        """
        current_conf = self.get()
        new_conf = current_conf.copy()
        new_conf.update(conf)
        return self.cimi.edit(RESOURCE_ID, new_conf)

