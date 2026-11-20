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


# ---------------------------------------------------------------------------
# Dry-run + subset logging (no network required)
# ---------------------------------------------------------------------------
import logging
from types import SimpleNamespace
from subscriber import subsetting


def _dry_run_subset_logs(caplog, granules=None):
    args = SimpleNamespace(dry_run=True, verbose=False)
    caplog.set_level(logging.INFO)
    result = subsetting.subset(
        collection_id='C1234-PROV',
        start_date_time='2020-01-01T00:00:00Z',
        end_date_time='2020-01-02T00:00:00Z',
        bbox='-180,-90,180,90',
        force=False,
        data_path='./unused',
        args=args,
        process_cmd=None,
        granules=granules,
    )
    return result, [r.getMessage() for r in caplog.records]


def test_dry_run_subset_still_logs_harmony_parameters(caplog):
    # Criterion 0: Collection ID, Start Time, End Time, BBox lines are still logged.
    _, messages = _dry_run_subset_logs(caplog)
    joined = "\n".join(messages)
    assert "Collection ID: C1234-PROV" in joined
    assert "Start Time:    2020-01-01T00:00:00Z" in joined
    assert "End Time:      2020-01-02T00:00:00Z" in joined
    assert "BBox:          -180,-90,180,90" in joined


def test_dry_run_subset_granules_line_is_explicit_not_bare_none(caplog):
    # Criterion 1: Granules line explains dry-run rather than showing bare "None".
    _, messages = _dry_run_subset_logs(caplog, granules=None)
    granule_lines = [m for m in messages if "Granules" in m]
    assert granule_lines, "expected a Granules line in dry-run output"
    line = granule_lines[0]
    assert not line.rstrip().endswith("None"), f"bare None shown: {line!r}"
    lowered = line.lower()
    assert "dry-run" in lowered or "dry run" in lowered
    assert "not searched" in lowered
    assert "subsetted" in lowered
