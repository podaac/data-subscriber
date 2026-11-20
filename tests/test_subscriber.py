from subscriber import podaac_data_subscriber as pds
from subscriber import podaac_access as pa

from urllib.error import HTTPError
import requests
import pytest
import os
from pathlib import Path
import shutil
import json
import tempfile
from os.path import exists
from packaging import version



def test_temporal_range():

    assert pa.get_temporal_range(None, '2021-01-01T00:00:00Z', "2021-08-20T13:30:38Z") == "1900-01-01T00:00:00Z,2021-01-01T00:00:00Z"
    assert pa.get_temporal_range('2021-01-01T00:00:00Z', '2022-01-01T00:00:00Z', "2021-08-20T13:30:38Z") == "2021-01-01T00:00:00Z,2022-01-01T00:00:00Z"
    assert pa.get_temporal_range('2021-01-01T00:00:00Z', None, "2021-08-20T13:30:38Z") == "2021-01-01T00:00:00Z,2021-08-20T13:30:38Z"
    with pytest.raises(ValueError):
        pa.get_temporal_range(None, None, None) == "2021-01-01T00:00:00Z,2021-08-20T13:30:38Z"



data_dir_with_updates = "./test_update_format_change"

@pytest.fixture
def cleanup_update_test():
    yield None
    print("Cleanup...")
    shutil.rmtree(data_dir_with_updates)

def test_create_citation_file():
    with tempfile.TemporaryDirectory() as tmpdirname:
        pa.create_citation_file("SWOT_SIMULATED_L2_KARIN_SSH_GLORYS_CALVAL_V1", "POCLOUD", tmpdirname)
        assert exists(tmpdirname+"/SWOT_SIMULATED_L2_KARIN_SSH_GLORYS_CALVAL_V1.citation.txt")

def test_citation_creation():
    collection_umm = '''{
        "DOI": {
            "DOI": "10.5067/KARIN-2GLC1",
            "Authority": "https://doi.org"
        },
        "CollectionCitations": [
            {
                "Creator": "SWOT",
                "ReleasePlace": "PO.DAAC",
                "Title": "SWOT Level-2 Simulated SSH from MITgcm LLC4320 Science Quality Version 1.0",
                "Publisher": "PO.DAAC",
                "ReleaseDate": "2022-01-31T00:00:00.000Z",
                "Version": "1.0"
            },
            {
                "Creator": "CNES/CLS",
                "ReleasePlace": "CNES/AVISO",
                "Title": "Simulated SWOT products",
                "OnlineResource": {
                    "Linkage": "http://doi.org/10.24400/527896/a01-2021.006",
                    "Name": " Simulated SWOT Sea Surface Height products",
                    "Description": "Simulated SWOT Sea Surface Height products KaRIn and Nadir.",
                    "MimeType": "text/html"
                },
                "Publisher": "PODAAC",
                "ReleaseDate": "2021-11-01T00:00:00.000Z",
                "Version": "1.0"
            }
        ]
    }
    '''
    collection_umm_json = json.loads(collection_umm)
    citation = pa.create_citation(collection_umm_json, "2022-07-21")
    assert citation == "SWOT. 2022. SWOT Level-2 Simulated SSH from MITgcm LLC4320 Science Quality Version 1.0. Ver. 1.0. PO.DAAC, CA, USA. Dataset accessed 2022-07-21 at https://doi.org/10.5067/KARIN-2GLC1"

def _swot_nalt_collection_umm(authority):
    return {
        "DOI": {
            "DOI": "10.5067/SWOT-NALT-IGDR-1.0",
            "Authority": authority
        },
        "CollectionCitations": [
            {
                "Creator": "SWOT",
                "ReleasePlace": "PO.DAAC",
                "Title": "SWOT Level-2 Nadir Altimeter IGDR",
                "Publisher": "PO.DAAC",
                "ReleaseDate": "2023-01-01T00:00:00.000Z",
                "Version": "1.0"
            }
        ]
    }


@pytest.mark.parametrize("authority", [
    "https://www.doi.org/",
    "https://www.doi.org//",
    "https://www.doi.org///",
])
def test_citation_doi_authority_trailing_slash_no_double_slash(authority):
    citation = pa.create_citation(_swot_nalt_collection_umm(authority), "2024-01-01")
    assert "at https://www.doi.org/10.5067/SWOT-NALT-IGDR-1.0" in citation
    assert "//10.5067" not in citation
    assert citation.endswith("at https://www.doi.org/10.5067/SWOT-NALT-IGDR-1.0")


def test_citation_doi_authority_without_trailing_slash_unchanged():
    citation = pa.create_citation(_swot_nalt_collection_umm("https://doi.org"), "2024-01-01")
    assert citation.endswith("Dataset accessed 2024-01-01 at https://doi.org/10.5067/SWOT-NALT-IGDR-1.0")


def test_search_after():
    # cmr query: https://cmr.earthdata.nasa.gov/search/granules.umm_json?page_size=2000&sort_key=-start_date&provider=POCLOUD&ShortName=JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F&temporal=2000-01-01T10%3A00%3A00Z%2C2022-04-15T00%3A00%3A00Z&bounding_box=-180%2C-90%2C180%2C90
    # requires page-After
    #  ends up with 3748 granules
    params = {
        'page_size': 2000,
        'sort_key': "-start_date",
        'provider': "POCLOUD",
        'ShortName': "JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F",
        'temporal': "2000-01-01T10:00:00Z,2022-04-15T00:00:00Z",
        'bounding_box': "-180,-90,180,90",
    }
    results = pa.get_search_results(params, True)
    # hits and items should always be more than 2000, ignoring page_size set
    assert results['hits'] > 2000
    assert len(results['items']) != 2000

def test_update_format_change(cleanup_update_test):
    print("Running Test")
    data_dir_with_updates = "./test_update_format_change"
    data_dir_with_no_updates = "./test_update_format_change_empty"

    collection_name_does_not_exist = "collectionNameNotfound"
    collection_name_exists = "collectionName"

    # Make directories and files...
    os.makedirs(data_dir_with_updates, exist_ok=True )
    Path(data_dir_with_updates+'/.update').touch()
    Path(data_dir_with_updates+'/.update__' + collection_name_exists).touch()

    assert pds.get_update_file(data_dir_with_no_updates, collection_name_does_not_exist) == None
    assert pds.get_update_file(data_dir_with_updates, collection_name_does_not_exist) == data_dir_with_updates+"/.update"
    assert pds.get_update_file(data_dir_with_updates, collection_name_exists) == data_dir_with_updates+'/.update__' + collection_name_exists

def test_validate():
    # work
    a = validate(["-c", "viirs", "-d", "/data"])
    assert a.collection == "viirs"
    assert a.outputDirectory == "/data"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90"])
    assert a.bbox == "-180,-90,180,90"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-170,-80,170,20"])
    assert a.bbox == "-170,-80,170,20"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-m", "100"])
    assert a.minutes == 100, "should equal 100"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-e", ".txt", "-e", ".nc"])
    assert ".txt" in a.extensions
    assert ".nc" in a.extensions

    a = validate(["-c", "viirs", "-d", "/data", "-dydoy", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
    assert a.outputDirectory == "/data"
    assert a.dydoy is True

    a = validate(["-c", "viirs", "-d", "/data", "-dymd", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
    assert a.outputDirectory == "/data"
    assert a.dymd is True

    a = validate(["-c", "viirs", "-d", "/data", "-dy", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
    assert a.outputDirectory == "/data"
    assert a.dy is True

    a = validate(["-c", "JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F", "-d", "/data", "-dc", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
    assert a.collection == "JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F"
    assert a.outputDirectory == "/data"
    assert a.cycle is True

    a = validate(["-c", "dataset", "-d", "/data", "-sd", "2020-01-01T00:00:00Z", "-ed", "2021-01-01T00:00:00Z"])
    assert a.startDate == '2020-01-01T00:00:00Z'
    assert a.endDate == '2021-01-01T00:00:00Z'
    assert a.provider == "POCLOUD"

    a = validate(["-c", "dataset", "-d", "/data", "-p", "ANEWCLOUD"])
    assert a.provider == 'ANEWCLOUD'

    with pytest.raises(ValueError):
        a = validate(["-c", "dataset", "-d", "/data", "-sd", "2020-01-01", "-ed", "2021-01-01T00:00:00Z"])

    with pytest.raises(ValueError):
        a = validate(["-c", "dataset", "-d", "/data", "-sd", "2020-01-01T00:00:00Z", "-ed", "2021-01-01"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90anc", "-m", "100"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90,100", "-m", "100"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180", "-m", "100"])

    # bbox crossing the IDL should not raise exception
    validate(["-c", "viirs", "-d", "/data", "-dy", "-e", ".nc", "-m", "60", "-b=120,-60,-120,60"])
    # valid bbox values should not raise exception
    validate(["-c", "viirs", "-d", "/data", "-dy", "-e", ".nc", "-m", "60", "-b=-180,-60,-120,60"])
    validate(["-c", "viirs", "-d", "/data", "-dy", "-e", ".nc", "-m", "60", "-b=-170,-20,-30,20"])

    # bbox with invalid latitude values should raise an exception
    with pytest.raises(ValueError):
        validate(["-c", "viirs", "-d", "/data", "-b=-180,90,180,-90", "-m", "100"])


    # #don't work
    # with pytest.raises(SystemExit):
    #     a = validate([])
    #
    # #don't work
    # with pytest.raises(SystemExit):
    #     a = validate(["-c", "viirs"])
    #
    # with pytest.raises(SystemExit):
    #     a = validate(["-d", "/data"])
    #
    # with pytest.raises(ValueError):
    #     a = validate(["-c", "viirs", "-d", "/data", "-ds", "2021-01-01T00:00:Z"])
    #
    # with pytest.raises(ValueError):
    #     a = validate(["-c", "viirs", "-d", "/data", "-b=-170abc,-80,170,20"])
    #
    # with pytest.raises(SystemExit):
    #     a = validate(["-c", "viirs", "-d", "/data", "-m","60b"])

def test_param_update():
    params = [
        ('sort_key', "-start_date"),
        ('provider', "'POCLOUD'"),
        ('token', "123"),
    ]

    for  i, p in enumerate(params) :
        if p[1] == "token":
            params[i] = ("token", "newToken")

    for i,p in enumerate(params) :
        if p[1] == "token":
            assert p[2] == "newToken"

def test_downloader_retry(mocker):
    response = requests.Response()
    response.status_code = 503
    error = requests.exceptions.HTTPError(response=response)
    mck = mocker.patch('subscriber.podaac_access.earthaccess.get_requests_https_session', side_effect=error)
    try:
        pa.download_file("myUrl", "outputPath")
    except Exception:
        pass
    assert mck.call_count == 3

def validate(args):
    parser = pds.create_parser()
    args2 = parser.parse_args(args)
    pa.validate(args2)
    return args2

def test_check_updates():
    version.parse(pa.get_latest_release())

def test_compare_release():
    tag="1.11.0"
    assert pa.release_is_current(tag,"1.11.0")
    assert pa.release_is_current(tag,"2.10.0")
    assert pa.release_is_current(tag,"1.11.1")

    assert not pa.release_is_current(tag,"1.10.0")
    assert not pa.release_is_current(tag,"1.10.5")
    assert not pa.release_is_current(tag,"0.9000.5")

def test_extensions():
    assert pa.search_extension('\\.tiff', "myfile.tiff") == True
    assert pa.search_extension('\\.tiff', "myfile.tif") == False
    assert pa.search_extension('\\.tiff', "myfile.gtiff") == False
    assert pa.search_extension('PTM_\\d+', "myfile.PTM_1") == True
    assert pa.search_extension('PTM_\\d+', "myfile.PTM_10") == True
    assert pa.search_extension('PTM_\\d+', "myfile.PTM_09") == True
    assert pa.search_extension('PTM_\\d+', "myfile.PTM_9") == True


def test_get_latest_release_from_json():
    f = open('tests/releases.json')
    release_json = json.load(f)
    latest_release = pa.get_latest_release_from_json(release_json)
    assert latest_release == "1.12.0"


# ---------------------------------------------------------------------------
# UAT / production CMR endpoint selection tests
# ---------------------------------------------------------------------------

PROD_CMR_HOST = "https://cmr.earthdata.nasa.gov"
UAT_CMR_HOST = "https://cmr.uat.earthdata.nasa.gov"


class _FakeResponse:
    def __init__(self, body=None):
        self._body = body if body is not None else {"items": [{"meta": {"concept-id": "C1-TEST"}}], "hits": 0}

    def read(self):
        return json.dumps(self._body).encode()

    def info(self):
        return {}


def _capture_urlopen(monkeypatch, body=None):
    captured = []

    def fake_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else req
        captured.append(url)
        return _FakeResponse(body)

    monkeypatch.setattr(pa, "urlopen", fake_urlopen)
    return captured


def test_uat_flag_parsed_by_create_parser():
    parser = pds.create_parser()
    args = parser.parse_args(["-c", "dataset", "-d", "/data", "-m", "60", "--uat"])
    assert args.uat is True


def test_no_uat_flag_defaults_to_production():
    parser = pds.create_parser()
    args = parser.parse_args(["-c", "dataset", "-d", "/data", "-m", "60"])
    assert getattr(args, "uat", False) is False


def test_granule_search_targets_uat_host_when_uat(monkeypatch):
    captured = _capture_urlopen(monkeypatch)
    params = [('provider', 'POCLOUD'), ('ShortName', 'dataset'), ('token', 'abc')]
    pa.get_search_results(params, False, uat=True)
    assert captured, "no CMR request was made"
    assert all(u.startswith(UAT_CMR_HOST) for u in captured)


def test_collection_search_targets_uat_host_when_uat(monkeypatch):
    captured = _capture_urlopen(monkeypatch)
    params = {'provider': 'POCLOUD', 'ShortName': 'dataset', 'token': 'abc'}
    pa.get_cmr_collections(params, False, uat=True)
    assert captured, "no CMR request was made"
    assert all(u.startswith(UAT_CMR_HOST) for u in captured)


def test_granule_search_targets_production_host_without_uat(monkeypatch):
    captured = _capture_urlopen(monkeypatch)
    params = [('provider', 'POCLOUD'), ('ShortName', 'dataset'), ('token', 'abc')]
    pa.get_search_results(params, False)
    assert captured, "no CMR request was made"
    assert all(u.startswith(PROD_CMR_HOST) for u in captured)
    assert not any("uat" in u for u in captured)


def test_collection_search_targets_production_host_without_uat(monkeypatch):
    captured = _capture_urlopen(monkeypatch)
    params = {'provider': 'POCLOUD', 'ShortName': 'dataset', 'token': 'abc'}
    pa.get_cmr_collections(params, False)
    assert captured, "no CMR request was made"
    assert all(u.startswith(PROD_CMR_HOST) for u in captured)
    assert not any("uat" in u for u in captured)


def test_uat_and_subset_rejected_during_validation():
    parser = pds.create_parser()
    args = parser.parse_args(["-c", "dataset", "-d", "/data", "-m", "60", "--uat", "--subset"])
    with pytest.raises(ValueError):
        pa.validate(args)
        pds.validate(args)


def test_uat_cmr_http_error_propagates(monkeypatch):
    def fake_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else req
        assert url.startswith(UAT_CMR_HOST)
        raise HTTPError(url, 500, "Server Error", {}, None)

    monkeypatch.setattr(pa, "urlopen", fake_urlopen)
    params = {'provider': 'POCLOUD', 'ShortName': 'dataset', 'token': 'abc'}
    with pytest.raises(HTTPError):
        pa.get_cmr_collections(params, False, uat=True)


def test_uat_collection_lookup_empty_raises_value_error(monkeypatch):
    monkeypatch.setattr(pa, "get_cmr_collections",
                        lambda *a, **k: {"items": []})
    with pytest.raises(ValueError):
        pa.get_cmr_collection_id("dataset", "POCLOUD", "abc", False, uat=True)


def test_uat_401_retry_targets_uat_host(monkeypatch):
    captured = []
    calls = {"n": 0}

    def fake_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else req
        captured.append(url)
        calls["n"] += 1
        if calls["n"] == 1:
            raise HTTPError(url, 401, "Unauthorized", {}, None)
        return _FakeResponse({"items": []})

    def fake_refresh_token(params=None):
        new_params = [(k, "newtoken" if k == "token" else v) for k, v in params]
        return "newtoken", new_params

    monkeypatch.setattr(pa, "urlopen", fake_urlopen)
    monkeypatch.setattr(pa, "refresh_token", fake_refresh_token)

    params = {'provider': 'POCLOUD', 'ShortName': 'dataset', 'token': 'abc'}
    pa.get_cmr_collections(params, False, uat=True)
    assert len(captured) >= 2
    assert all(u.startswith(UAT_CMR_HOST) for u in captured)
