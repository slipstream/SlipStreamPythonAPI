from pprint import pprint as pp

from .log import Logger

RESOURCE_ID = 'configuration/slipstream'


class Configuration(Logger):

    def __init__(self, cimi):
        super(Configuration, self).__init__()
        self.cimi = cimi

    def get(self):
        return self.cimi.get(RESOURCE_ID)

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
