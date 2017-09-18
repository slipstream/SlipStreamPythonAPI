import pytest
from six import string_types
import fixtures


def setup_function():
    pass


def teardown_function():
    fixtures.cleanup()


@pytest.mark.live
def test_login_logout_internal_lifecycle():
    cimi = fixtures.get_cimi(no_login=True)
    login_params = fixtures.get_login_params()
    login_internal = login_params and login_params['href'].endswith('internal')

    if not (cimi and login_internal):
        pytest.skip("CIMI client and login params are not defined.")

    assert None is cimi.current_session()
    assert False is cimi.is_authenticated()
    res = cimi.login(login_params)
    assert 201 == res.get('status')
    session_id = cimi.current_session()
    assert isinstance(session_id, string_types) and len(session_id) > 0
    assert True is cimi.is_authenticated()
    res = cimi.logout()
    assert 200 == res.get('status')
    assert False is cimi.is_authenticated()
