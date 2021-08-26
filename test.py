from subscriber import podaac_data_subscriber as pds
import pytest


def test_temporal_range():
    assert pds.get_temporal_range(None,'2021-01-01T00:00:00Z',"2021-08-20T13:30:38Z") == "1900-01-01T00:00:00Z,2021-01-01T00:00:00Z"
    assert pds.get_temporal_range('2021-01-01T00:00:00Z','2022-01-01T00:00:00Z',"2021-08-20T13:30:38Z") == "2021-01-01T00:00:00Z,2022-01-01T00:00:00Z"
    assert pds.get_temporal_range('2021-01-01T00:00:00Z',None,"2021-08-20T13:30:38Z") == "2021-01-01T00:00:00Z,2021-08-20T13:30:38Z"
    with pytest.raises(ValueError):
        pds.get_temporal_range(None,None,None) == "2021-01-01T00:00:00Z,2021-08-20T13:30:38Z"


def test_validate():
    #work
    a = validate(["-c", "viirs", "-d", "/data"])
    assert a.collection == "viirs"
    assert a.outputDirectory == "/data"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90"])
    assert a.bbox == "-180,-90,180,90"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-170,-80,170,20"])
    assert a.bbox == "-170,-80,170,20"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-m","100"])
    assert a.minutes == 100, "should equal 100"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-e", ".txt", ".nc"])
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

    with pytest.raises(ValueError):
        a = validate(["-c", "dataset", "-d", "/data", "-sd", "2020-01-01", "-ed", "2021-01-01T00:00:00Z"])

    with pytest.raises(ValueError):
        a = validate(["-c", "dataset", "-d", "/data", "-sd", "2020-01-01T00:00:00Z", "-ed", "2021-01-01"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90anc", "-m","100"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90,100", "-m","100"])

    with pytest.raises(ValueError):
        a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180", "-m","100"])

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


def validate(args):
    parser = pds.create_parser()
    args2 = parser.parse_args(args)
    pds.validate(args2)
    return args2
