import pytest

from slipstream.api.configuration import _connector_classes_str_to_dict
from slipstream.api.configuration import get_cloud_connector_classes
from slipstream.api.configuration import SERVER_CONFIGURATION_BASICS_CATEGORY
from slipstream.api.configuration import \
    SERVER_CONFIGURATION_CONNECTOR_CLASSES_KEY

pytestmark = pytest.mark.local


def test_connector_classes_str_to_dict():
    assert {} == _connector_classes_str_to_dict('')
    assert {'foo': 'foo'} == _connector_classes_str_to_dict('foo')
    assert {'foo': 'bar'} == _connector_classes_str_to_dict('foo:bar')

    res = _connector_classes_str_to_dict('foo:bar, baz')
    unmatched_items = set([('foo', 'bar'), ('baz', 'baz')]) ^ set(res.items())
    assert 0 == len(unmatched_items)


def test_get_cloud_connector_classes_from_basics_category():
    assert {} == get_cloud_connector_classes({})
    assert {} == get_cloud_connector_classes({'foo': 'bar'})
    assert {} == get_cloud_connector_classes(
        {SERVER_CONFIGURATION_BASICS_CATEGORY: []})
    assert {} == get_cloud_connector_classes(
        {SERVER_CONFIGURATION_BASICS_CATEGORY: [(), ]})
    assert {} == get_cloud_connector_classes(
        {SERVER_CONFIGURATION_BASICS_CATEGORY: [('', ''), ]})

    conf = {SERVER_CONFIGURATION_BASICS_CATEGORY: [
        (SERVER_CONFIGURATION_CONNECTOR_CLASSES_KEY, ''), ]}
    assert {} == get_cloud_connector_classes(conf)

    conf = {SERVER_CONFIGURATION_BASICS_CATEGORY: [
        (SERVER_CONFIGURATION_CONNECTOR_CLASSES_KEY, 'foo'), ]}
    assert {'foo': 'foo'} == get_cloud_connector_classes(conf)
