import pytest
import time
from slipstream.api.configuration import Configuration

from slipstream.api.defaults import DEFAULT_ENDPOINT
from slipstream.api.cimi import CIMI
from slipstream.api.http import SessionStore

# Don't commit credentials!
username = 'super'
password = None
endpoint = DEFAULT_ENDPOINT
insecure = False

password = '25e80cc651b2'
endpoint = 'https://185.19.29.150'
insecure = True


@pytest.mark.live
def test_cimi_edit():
    if not (username and password):
        pytest.skip("Credentials are not provided.")
    cimi = CIMI(SessionStore(insecure=insecure), endpoint=endpoint)
    cimi.login_internal(username, password)
    c = Configuration(cimi)
    ct = str(time.time())
    new = {'description': ct}
    updated = c.edit(new)
    assert ct == updated.get('description')
