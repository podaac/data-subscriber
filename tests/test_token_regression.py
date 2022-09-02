import pytest
import os
from os.path import exists

from subscriber import podaac_access as pa
import shutil
from pathlib import Path


def setup_module(module):
    print('*****SETUP*****')
    tokens = pa.list_tokens(pa.token_url)
    for x in tokens:
        pa.delete_token(pa.token_url, x)

def teardown_module(module):
    print('*****TEARDOWN*****')
    tokens = pa.list_tokens(pa.token_url)
    for x in tokens:
        pa.delete_token(pa.token_url, x)

# REGRESSION TEST CURRENTLY REQUIRES A .NETRC file for CMR/Data Download
# token API can be found here: https://wiki.earthdata.nasa.gov/display/EL/API+Documentation
# explore https://urs.earthdata.nasa.gov/documentation/for_integrators/api_documentation#/oauth/token
def test_list_tokens():
    tokens = pa.list_tokens(pa.token_url)
    for x in tokens:
        pa.delete_token(pa.token_url, x)

def test_edl_getToken():
    token = pa.get_token(pa.token_url)
    assert token != ""
    token = pa.refresh_token(token)
    assert token != ""
    tokens = pa.list_tokens(pa.token_url)

    assert len(tokens) == 1
    for x in tokens:
        assert x != ""

    assert True == pa.delete_token(pa.token_url, token)

def test_edl_max_token():
    #call this 3 times since we're capped out at 2 total...
    token = pa.get_token(pa.token_url)
    assert token != ""
    token = pa.get_token(pa.token_url)
    assert token != ""
    token = pa.get_token(pa.token_url)
    assert token != ""
