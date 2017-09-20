import pytest
from mock import Mock
from slipstream.api.cimi import CIMI

pytestmark = pytest.mark.local


def test_split_params():
    cimi, other = CIMI._split_params({})
    assert cimi == {}
    assert other == {}


def test_get_base_uri():
    cimi = CIMI(Mock())
    baseuri = 'http://foo/bar'
    cimi._get_cloud_entry_point = Mock(return_value={'baseURI': baseuri})
    assert baseuri == cimi.base_uri


def test_to_url():
    cimi = CIMI(Mock())
    baseuri = 'http://foo/bar/'
    cimi._get_cloud_entry_point = Mock(return_value={'baseURI': baseuri})
    assert 'http://foo/bar' == cimi._to_url('http://foo/bar')
    assert 'https://foo/bar' == cimi._to_url('https://foo/bar')
    assert '%sbaz' % baseuri == cimi._to_url('/baz')


def test_get_resource_entry_point():
    cimi = CIMI(Mock())
    cimi._get_cloud_entry_point = Mock(return_value=
                                       {'fooBar': {'href': 'foo-bar'}})
    assert 'foo-bar' == cimi.get_resource_href('fooBar')
    with pytest.raises(KeyError) as excinfo:
        cimi.get_resource_href('fooType')
    assert 'fooType' in str(excinfo.value)
