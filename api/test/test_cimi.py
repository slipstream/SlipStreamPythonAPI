from slipstream.api.cimi import CIMI


def test_split_params():
    cimi, other = CIMI._split_params({})
    assert cimi == {}
    assert other == {}
