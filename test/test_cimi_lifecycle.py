from slipstream.api.defaults import DEFAULT_ENDPOINT
from slipstream.api.cimi import CIMI
from slipstream.api.http import SessionStore

# Don't commit credentials!
username = None
password = None
endpoint = DEFAULT_ENDPOINT
insecure = False


def test_login_logout_internal():
    if not (username and password):
        return
    cimi = CIMI(SessionStore(insecure=insecure), endpoint=endpoint)
    res = cimi.login_internal(username, password)
    assert 201 == res.status
    assert True is cimi.is_authenticated()
    res = cimi.logout()
    assert 200 == res.status
    assert False is cimi.is_authenticated()
