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
    args = create_downloader_args(f"-c TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4 -sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:01Z -d {str(tmpdir)} --limit 1 --verbose".split())
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

@pytest.mark.regression
def test_downloader_temporal_and_granule_together():
    # Command: podaac-data-downloader -c TRPSDL2ALLCRSMGLOS -d data -p GES_DISC -sd 2020-01-01T00:00:00Z -ed 2020-01-02T23:59:59Z -gr *NH3*
    shutil.rmtree('./TMP', ignore_errors=True)
    args2 = create_downloader_args(
        '-c TRPSDL2ALLCRSMGLOS -d ./TMP -p GES_DISC -sd 2020-01-01T00:00:00Z -ed 2020-01-02T23:59:59Z -gr *NH3*'
        .split())
    pdd.run(args2)
    # So running the test in parallel, sometimes we get a 401 on the token...
    # Let's ensure we're only looking for data files here
    assert len([name for name in os.listdir('./TMP') if
                os.path.isfile('./TMP/' + name) and "citation.txt" not in name]) == 2
    shutil.rmtree('./TMP')


# ---------------------------------------------------------------------------
# Dry-run + subset output (mocked, no network required)
# ---------------------------------------------------------------------------
import logging


def _run_dry_run_subset(monkeypatch, tmp_path, caplog):
    from subscriber import subsetting as sub

    monkeypatch.setattr(pdd.pa, 'validate', lambda args: None)
    monkeypatch.setattr(pdd.pa, 'refresh_token', lambda: 'token')
    monkeypatch.setattr(pdd.pa, 'get_cmr_collection_id', lambda **kw: 'C1234-PROV')
    monkeypatch.setattr(sub, 'is_subsettable', lambda **kw: True)
    monkeypatch.setattr(pdd.pa, 'create_citation_file', lambda *a, **k: None)

    args = create_downloader_args(
        f'-c SOME_COLL -d {tmp_path} --dry-run --subset '
        '-sd 2020-01-01T00:00:00Z -ed 2020-01-02T00:00:00Z -b=-180,-90,180,90'.split())
    caplog.set_level(logging.INFO)
    pdd.run(args)
    return [r.getMessage() for r in caplog.records]


def test_dry_run_subset_success_count_not_bare_zero(monkeypatch, tmp_path, caplog):
    # Criterion 2: Success Count line states count not applicable in dry-run.
    messages = _run_dry_run_subset(monkeypatch, tmp_path, caplog)
    success_lines = [m for m in messages if "Success Count" in m]
    assert success_lines, "expected a Success Count line"
    line = success_lines[0]
    assert line.strip() != "Success Count: 0"
    assert not line.rstrip().endswith(": 0")
    lowered = line.lower()
    assert "not applicable" in lowered or "dry-run" in lowered or "dry run" in lowered


def test_dry_run_subset_no_zero_granules_or_failure_wording(monkeypatch, tmp_path, caplog):
    # Criterion 3: no message implies zero granules found or subset failure.
    messages = _run_dry_run_subset(monkeypatch, tmp_path, caplog)
    joined = "\n".join(messages).lower()
    assert "found 0" not in joined
    assert "no granules" not in joined
    assert "fail" not in joined
