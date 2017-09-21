import os
import tempfile
import logging
from six.moves import configparser

from slipstream.api.cimi import CIMI
from slipstream.api.http import SessionStore
from slipstream.api.defaults import DEFAULT_ENDPOINT

config_file = 'test/test.conf'
cookie_file = None
SECTION = 'contextualization'


def mk_cookie_file():
    global cookie_file
    tf = tempfile.NamedTemporaryFile()
    tf.close()
    cookie_file = tf.name


def del_cookie_file():
    global cookie_file
    if cookie_file:
        try:
            os.unlink(cookie_file)
        except:
            pass


def get_login_params():
    config = read_config()

    method = config.get(SECTION, 'method')
    login_params = {}
    if method == 'internal':
        username = config.get(SECTION, 'username')
        password = config.get(SECTION, 'password')
        if username and password:
            login_params = {'href': 'session-template/%s' % method,
                            'username': username,
                            'password': password}
    elif method == 'api-key':
        key = config.get(SECTION, 'key')
        secret = config.get(SECTION, 'secret')
        if key and secret:
            login_params = {'href': 'session-template/%s' % method,
                            'key': key,
                            'secret': secret}
    return login_params


def get_config():
    config = read_config()

    endpoint = config.get(SECTION, 'endpoint')
    insecure = config.get(SECTION, 'insecure')
    log_level = logging.getLevelName(config.get(SECTION, 'log_level'))

    login_params = get_login_params()

    return login_params, endpoint, insecure, log_level


def read_config():
    config = configparser.ConfigParser(defaults={'endpoint': DEFAULT_ENDPOINT,
                                                 'insecure': False,
                                                 'log_level': logging.INFO})
    config.read(config_file)
    return config


def get_cimi(no_login=False):
    global cookie_file
    login_params, endpoint, insecure, log_level = get_config()
    if not login_params:
        return
    mk_cookie_file()
    cimi = CIMI(SessionStore(cookie_file=cookie_file,
                             insecure=insecure,
                             log_http_detail=(log_level == logging.DEBUG)),
                endpoint=endpoint)
    if no_login:
        return cimi
    else:
        cimi.login(login_params)
        return cimi


def cleanup():
    del_cookie_file()
