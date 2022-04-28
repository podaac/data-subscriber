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

#Test the downlaoder on MUR25 data for start/stop/, yyyy/mmm/dd dir structure,
# and offset. Running it a second time to ensure it downlaods the files again-
# the downloader doesn't care about updates.
@pytest.mark.regression
def test_downloader_MUR():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4'.split())
    pdd.run(args2)
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert exists('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    t1 = os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    t2 = os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    # this part of the test should not re-download the files unless the --force
    # option is used.
    pdd.run(args2)
    assert t1 == os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert t2 == os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    # Update a file to change the checksum, then re-download
    os.remove('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    Path('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc').touch()
    pdd.run(args2)
    assert t1 != os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert t2 == os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')
