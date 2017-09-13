import pytest
from slipstream.api.deployment import to_param_id, PARAMETER_RESOURCE, \
    PARAMETER_SEPAR

pytestmark = pytest.mark.local


def test_to_param_id():
    id = to_param_id('123', 'foo', 1, 'bar')
    assert id.startswith(PARAMETER_RESOURCE)
    assert 4 == len(id.replace(PARAMETER_RESOURCE, '').split(PARAMETER_SEPAR))
