import pytest

from subscriber import podaac_access as pa

# REGRESSION TEST CURRENTLY REQUIRES A .NETRC file for CMR/Data Download
# token API can be found here: https://wiki.earthdata.nasa.gov/display/EL/API+Documentation
# explore https://urs.earthdata.nasa.gov/documentation/for_integrators/api_documentation#/oauth/token
@pytest.mark.token
def test_edl_getToken():
    token = pa.get_token()
    assert token != ""
    token = pa.refresh_token(token)
    assert token != ""

    assert True is pa.delete_token(pa.token_url, token)