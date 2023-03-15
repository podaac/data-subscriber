import pytest
import os
from os.path import exists
from subscriber import podaac_data_subscriber as pds
from subscriber import podaac_data_downloader as pdd
import shutil

# REGRESSION TEST CURRENTLY REQUIRES A .NETRC file for CMR/Data Download
#
def create_args(args):
    parser = pds.create_parser()
    args2 = parser.parse_args(args)
    return args2

# Test to download ECCO data by start/stop date and put it in the year/doy dir
# structure.
@pytest.mark.regression
def test_subscriber_ecco_only_enddate():
    args2 = create_args('-c ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4 -ed 1992-01-03T00:00:00Z -d ./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4  -dydoy'.split())
    pds.run(args2)
    assert exists('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4/1992/001/ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-01_ECCO_V4r4_latlon_0p50deg.nc')
    assert exists('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4/1992/002/ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-02_ECCO_V4r4_latlon_0p50deg.nc')
    assert exists('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4/1992/003/ATM_SURFACE_TEMP_HUM_WIND_PRES_day_mean_1992-01-03_ECCO_V4r4_latlon_0p50deg.nc')
    shutil.rmtree('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4')

# Test to ensure nothing is downloaded via dry-run
@pytest.mark.regression
def test_subscriber_ecco_dry_run():
    args2 = create_args('-c ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4 -ed 1992-01-03T00:00:00Z -d ./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4  -dydoy --dry-run'.split())
    pds.run(args2)
    assert len(os.listdir('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4')) == 0 
    shutil.rmtree('./ECCO_L4_ATM_STATE_05DEG_DAILY_V4R4')

# test to download S6 data by start/stop time, and bbox, and put it in the
# cycle based directory structure
@pytest.mark.regression
def test_subscriber_cycle_bbox():
    args2 = create_args('-c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F -d ./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -dc -sd 2022-01-01T00:00:00Z -ed 2022-01-02T00:00:00Z -b=-20,-20,20,20'.split())
    pds.run(args2)
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/c0042/S6A_P4_2__LR_STD__NR_042_071_20211231T232728_20220101T012144_F04.nc')
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/c0042/S6A_P4_2__LR_STD__NR_042_082_20220101T090557_20220101T104242_F04.nc')
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/c0042/S6A_P4_2__LR_STD__NR_042_083_20220101T104242_20220101T123506_F04.nc')
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/c0042/S6A_P4_2__LR_STD__NR_042_095_20220101T215702_20220101T234905_F04.nc')
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/c0042/S6A_P4_2__LR_STD__NR_042_097_20220101T234905_20220102T014431_F04.nc')
    assert exists('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F/.update__JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F')
    shutil.rmtree('./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F')

# Test to download MUR25 data by start/stop, put it in yyyy/mm/dd dir structure,
# using the offset so it aligns with the right day in the filename.
#
# Test will run it again, to ensure that the files are not re-downlaoded, that
# is, they have the same modified time before/after the second run
@pytest.mark.regression
def test_subscriber_MUR_update_file_no_redownload():
    try:
        os.remove('MUR25-JPL-L4-GLOB-v04.2/.update')
    except OSError as e:
        print("Expecting this...")
    try:
        os.remove('MUR25-JPL-L4-GLOB-v04.2/..update__MUR25-JPL-L4-GLOB-v04.2')
    except OSError as e:
        print("Expecting this...")

    args2 = create_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4 --verbose'.split())
    pds.run(args2)
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/.update__MUR25-JPL-L4-GLOB-v04.2')
    t1 = os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    t2 = os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    # Compare another run to existing times to ensure it didn't redownload the file
    pds.run(args2)
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/.update__MUR25-JPL-L4-GLOB-v04.2')
    assert t1 == os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert t2 == os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')
