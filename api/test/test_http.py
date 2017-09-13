import pytest
from mock import Mock
from slipstream.api.http import set_stream_header, HEADER_SSE, \
    is_streamed_response, SessionStore, HTTP_TIMEOUTS, HTTP_CONNECT_TIMEOUT, \
    HTTP_READ_TIMEOUT_SSE, HTTP_TIMEOUTS_SSE

pytestmark = pytest.mark.local


def test_set_stream_header():
    assert {'Accept': HEADER_SSE} == set_stream_header({})

    headers = {'foo': 'bar'}
    hset = set(headers)
    hstream = set_stream_header(headers)
    assert set(hstream).symmetric_difference(hset) == {'Accept'}
    assert HEADER_SSE == hstream['Accept']
    assert 'foo' in hstream
    assert 'bar' == hstream['foo']

    headers = {'foo': 'bar', 'accept': 'text/plain'}
    hset = set(headers)
    hstream = set_stream_header(headers)
    assert set(hstream).symmetric_difference(hset) == set()
    assert 'text/plain, %s' % HEADER_SSE == hstream['accept']
    assert 'foo' in hstream
    assert 'bar' == hstream['foo']


def test_is_streamed_response():
    assert False is is_streamed_response(None)

    response = Mock()
    response.ok = False
    assert False is is_streamed_response(response)

    response = Mock()
    response.ok = True
    response.request = Mock()
    response.request.headers = {}
    assert False is is_streamed_response(response)

    response.request.headers = {'foo': 'bar', 'accept': ''}
    assert False is is_streamed_response(response)

    response.request.headers = {'foo': 'bar', 'accept': HEADER_SSE}
    assert True is is_streamed_response(response)

    response.request.headers = {'foo': 'bar', 'Accept': 'a/b, ' + HEADER_SSE}
    assert True is is_streamed_response(response)


def test_update_request_params():
    params = {}
    SessionStore._update_request_params(params)
    assert 'timeout' in params
    assert params['timeout'] == HTTP_TIMEOUTS

    params = {'foo': 'bar'}
    SessionStore._update_request_params(params)
    assert 'foo' in params
    assert 'timeout' in params
    assert params['timeout'] == HTTP_TIMEOUTS

    params = {'timeout': (1., 1.)}
    SessionStore._update_request_params(params)
    assert 'timeout' in params
    assert params['timeout'] == (1., 1.)

    # Anything other than a tuple or list is treated as read timeout.
    for rt in ['1.', 1.]:
        params = {'timeout': rt}
        SessionStore._update_request_params(params)
        assert 'timeout' in params
        assert params['timeout'] == (HTTP_CONNECT_TIMEOUT, float(rt))

    params = {'timeout': 1., 'stream': True}
    SessionStore._update_request_params(params)
    assert 'timeout' in params
    assert params['timeout'] == (HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT_SSE)

    params = {'stream': True}
    SessionStore._update_request_params(params)
    assert 'timeout' in params
    assert params['timeout'] == HTTP_TIMEOUTS_SSE
