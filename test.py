from subscriber import podaac_data_subscriber as pds
import pytest


def test_validate():
    #work
    a = validate(["-c", "viirs", "-d", "/data"])
    assert a.dataSince == False
    assert a.collection == "viirs"
    assert a.outputDirectory == "/data"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90"])
    assert a.bbox == "-180,-90,180,90"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-170,-80,170,20"])
    assert a.bbox == "-170,-80,170,20"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-ds", "2021-01-01T00:00:00Z"])
    assert a.dataSince == "2021-01-01T00:00:00Z"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-m","100"])
    assert a.minutes == 100, "should equal 100"

    a = validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-e", ".txt", ".nc"])
    assert ".txt" in a.extensions
    assert ".nc" in a.extensions

    a = validate(["-c", "viirs", "-dydoy", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
    assert a.outputDirectory is None
    assert a.dydoy is True

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
