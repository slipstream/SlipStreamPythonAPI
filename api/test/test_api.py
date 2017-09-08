from slipstream.api.api import get_module_type


def test_get_module_type():
    assert 'component' == get_module_type('image')
