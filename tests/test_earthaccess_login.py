import pytest
import earthaccess
from subscriber import podaac_access as pa


@pytest.mark.token
def test_earthaccess_login_with_netrc():
    auth = earthaccess.login(strategy="netrc")
    assert (
        auth.authenticated
    ), "earthaccess could not authenticate against EDL via netrc"


@pytest.mark.token
def test_earthaccess_edl_token_fetch():
    earthaccess.login(strategy="netrc")
    token = earthaccess.get_edl_token()
    assert token and token.get("access_token"), "EDL did not return an access token"


@pytest.mark.token
def test_podaac_access_refresh_token():
    earthaccess.login(strategy="netrc")
    first_token = earthaccess.get_edl_token()
    assert first_token and first_token.get(
        "access_token"
    ), "EDL did not return an access token"

    # mock params to test refresh_token
    params = [("token", first_token.get("access_token")), ("test", "test")]
    token, updated_params = pa.refresh_token(params)

    # check that we forced a token fetch
    assert (
        token and updated_params
    ), "refresh_token didn't return token and updated params"
    assert token != first_token, "EDL did not fetch a new access token"

    # check
    param_keys = [param[0] for param in updated_params]
    assert "token" in param_keys, "No token in the returned params!"
    assert (
        token == [param[1] for param in updated_params if param[0] == "token"][0]
    ), "Token in returned params doesn't match new token"
