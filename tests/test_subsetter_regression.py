import pytest
import os
from os.path import exists
from subscriber import podaac_data_downloader as pdd
import shutil
from pathlib import Path

# REGRESSION TEST CURRENTLY REQUIRES A .NETRC file for CMR/Data Download

def create_downloader_args(args):
    parser = pdd.create_parser()
    args2 = parser.parse_args(args)
    return args2


# No subsetter
# -c VIIRS_N20-STAR-L2P-v2.80 -d ./data -b="52,52,55,55" -sd 2020-06-01T00:46:02Z -ed 2020-06-02T00:46:02Z --verbose --subset --limit 1

# Valid Subsetters
# -c MODIS_A-JPL-L2P-v2019.0  -d ./data -b="52,52,55,55" -sd 2020-06-01T00:46:02Z -ed 2020-06-02T00:46:02Z --verbose --subset --limit 1 --verbose --force
# -c AMSR2-REMSS-L2P-v8.2 -d ./data -b="52,52,55,55" -sd 2020-06-01T00:46:02Z -ed 2020-06-02T00:46:02Z --verbose --subset --limit 1
# -c SWOT_SIMULATED_L2_KARIN_SSH_GLORYS_SCIENCE_V1  -d ./data -b="-125.469,15.820,-99.453,35.859" -sd 2014-03-10T00:46:02Z -ed 2014-05-16T00:46:02Z --verbose --subset
# -c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -d ./data -b="-125.469,15.820,-99.453,35.859" -sd 2023-03-10T00:46:02Z -ed 2023-03-16T00:46:02Z --verbose --subset


#Test the downlaoder on MUR25 data for start/stop/, yyyy/mmm/dd dir structure,
# and offset. Running it a second time to ensure it downlaods the files again-
# the downloader doesn't care about updates.
@pytest.mark.regression
def test_subset_MUR_by_name():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -gr 20221206090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc --verbose'.split())
    pdd.run(args2)
    # So running the test in parallel, sometimes we get a 401 on the token...
    # Let's ensure we're only looking for data files here
    assert len([name for name in os.listdir('./MUR25-JPL-L4-GLOB-v04.2') if os.path.isfile('./MUR25-JPL-L4-GLOB-v04.2/' + name) and "citation.txt" not in name ])==1
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')
