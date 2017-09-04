from slipstream.api.http import set_stream_header, HEADER_SSE


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
