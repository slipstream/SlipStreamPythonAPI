import pytest
import json
import fixtures
import threading
from six import string_types
import time
from slipstream.api.deployment import Deployment

cimi = None


def setup_function():
    global cimi
    cimi = fixtures.get_cimi()


def teardown_function():
    global cimi
    fixtures.cleanup()
    cimi = None


@pytest.mark.live
def test_get_state():
    if not cimi:
        pytest.skip("CIMI client not defined.")
    dpl = Deployment(cimi, 'dfd34916-6ede-47f7-aaeb-a30ddecbba5b')
    val = dpl.state()
    assert isinstance(val, string_types)


@pytest.mark.live
def test_get_deployment_parameter():
    if not cimi:
        pytest.skip("CIMI client not defined.")
    dpl = Deployment(cimi, 'dfd34916-6ede-47f7-aaeb-a30ddecbba5b')
    val = dpl.get_deployment_parameter('node1', 1, 'vmstate')
    assert isinstance(val, string_types)


@pytest.mark.live
def test_get_deployment_parameter_sse():
    if not cimi:
        pytest.skip("CIMI client not defined.")
    dpl = Deployment(cimi, 'dfd34916-6ede-47f7-aaeb-a30ddecbba5b')
    val_to_set = str(time.time())
    val_to_get = None
    set_param = threading.Thread(
        group=None,
        target=dpl.set_deployment_parameter,
        name='set deployment parameter',
        args=('node1', 1, 'vmstate', val_to_set),
        kwargs={})
    with dpl.get_deployment_parameter('node1', 1, 'vmstate', stream=True) as res:
        set_param.start()
        for e in res.events():
            if e.data:
                val_to_get = json.loads(e.data).get('value')
            else:
                raise Exception('This should have never been called.')
    assert val_to_set == val_to_get
    set_param.join()