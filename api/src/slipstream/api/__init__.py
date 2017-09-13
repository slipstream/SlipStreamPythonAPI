# following PEP 386
__version__ = '${project.version}'

# FIXME: This breaks loading of modules like: import slipstream.api.models
#        In turn, this change breaks slipstream-cli.
# from .api import Api, SlipStreamError
