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
def test_downloader_MUR_by_name():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -gr 20221206090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc --verbose'.split())
    pdd.run(args2)
    # So running the test in parallel, sometimes we get a 401 on the token...
    # Let's ensure we're only looking for data files here
    assert len([name for name in os.listdir('./MUR25-JPL-L4-GLOB-v04.2') if os.path.isfile('./MUR25-JPL-L4-GLOB-v04.2/' + name) and "citation.txt" not in name ])==1
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')

# Test the downlaoder on SWOT Simulated single file download
@pytest.mark.regression
def test_downloader_limit_MUR():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-30T00:00:00Z --limit 1 --verbose'.split())
    pdd.run(args2)
    # So running the test in parallel, sometimes we get a 401 on the token...
    # Let's ensure we're only looking for data files here
    assert len([name for name in os.listdir('./MUR25-JPL-L4-GLOB-v04.2') if os.path.isfile('./MUR25-JPL-L4-GLOB-v04.2/' + name) and "citation.txt" not in name ])==1
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')

# Test the downlaoder on SWOT Simulated single file download
@pytest.mark.regression
def test_downloader_limit_dry_run():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2 --dry-run  -sd 2020-01-01T00:00:00Z -ed 2020-01-30T00:00:00Z --limit 1 --verbose'.split())
    pdd.run(args2)
    # So running the test in parallel, sometimes we get a 401 on the token...
    # Let's ensure we're only looking for data files here
    assert len([name for name in os.listdir('./MUR25-JPL-L4-GLOB-v04.2') if os.path.isfile('./MUR25-JPL-L4-GLOB-v04.2/' + name) and "citation.txt" not in name ])==0
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')


#Test the downlaoder on MUR25 data for start/stop/, yyyy/mmm/dd dir structure,
# and offset. Running it a second time to ensure it downlaods the files again-
# the downloader doesn't care about updates.
@pytest.mark.regression
def test_downloader_MUR():
    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2', ignore_errors=True)
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4 --verbose'.split())
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

    t1 = os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    # Set the args to --force to re-download those data
    args2 = create_downloader_args('-c MUR25-JPL-L4-GLOB-v04.2 -d ./MUR25-JPL-L4-GLOB-v04.2  -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -dymd --offset 4 -f --verbose'.split())
    pdd.run(args2)
    assert t1 != os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/01/20200101090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')
    assert t2 != os.path.getmtime('./MUR25-JPL-L4-GLOB-v04.2/2020/01/02/20200102090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc')

    shutil.rmtree('./MUR25-JPL-L4-GLOB-v04.2')


@pytest.mark.regression
def test_downloader_GRACE_with_SHA_512(tmpdir):
    # start with empty directory
    directory_str = str(tmpdir)
    assert len( os.listdir(directory_str) ) == 0

    # run the command once -> should download the file. Note the modified time for the file
    args = create_downloader_args(f"-c GRACEFO_L2_CSR_MONTHLY_0060 -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:01Z -d {str(tmpdir)} --limit 1 --verbose -e 00".split())
    pdd.run(args)
    assert len( os.listdir(directory_str) ) > 0
    filename = directory_str + "/" + os.listdir(directory_str)[0]
    #if the citation file was chosen above, get the next file since citation file is updated on successful run
    if "citation.txt" in filename:
        filename = directory_str + "/" + os.listdir(directory_str)[1]

    modified_time_1 = os.path.getmtime(filename)
    print( modified_time_1 )

    # run the command again -> should not redownload the file. The modified time for the file should not change
    pdd.run(args)
    modified_time_2 = os.path.getmtime(filename)
    print( modified_time_2 )
    assert modified_time_1 == modified_time_2
