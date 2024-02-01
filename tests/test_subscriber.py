from subscriber import podaac_data_subscriber as pds
from subscriber import podaac_access as pa

from urllib.error import HTTPError
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
    assert results['hits'] == 3762
    assert len(results['items']) == 3762

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
    mck = mocker.patch('subscriber.podaac_access.urlretrieve', side_effect=HTTPError("url", 503, "msg", None, None))
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
