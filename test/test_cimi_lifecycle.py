from slipstream.api.cimi import CIMI
from slipstream.api.http import SessionStore

# Don't commit credentials!
username = None
password = None


def test_login_logout_internal():
    if not (username and password):
        return
    cimi = CIMI(SessionStore())
    res = cimi.login_internal(username, password)
    assert 201 == res.status
    assert True is cimi.is_authenticated()
    res = cimi.logout()
    assert 200 == res.status
    assert False is cimi.is_authenticated()
