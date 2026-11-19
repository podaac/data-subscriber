import logging
from argparse import Namespace

from subscriber import subsetting
from subscriber import podaac_data_downloader as pdd


COLLECTION = "C1234-PROV"
START = "2023-01-01T00:00:00Z"
END = "2023-01-02T00:00:00Z"
BBOX = "-10,-10,10,10"


def _dry_run_args(**overrides):
    args = Namespace(dry_run=True, verbose=False, force=False, process_cmd=None)
    for k, v in overrides.items():
        setattr(args, k, v)
    return args


def _messages(caplog):
    return [r.getMessage() for r in caplog.records]


def _call_dry_run_subset(**kwargs):
    return subsetting.subset(
        collection_id=COLLECTION,
        start_date_time=START,
        end_date_time=END,
        bbox=BBOX,
        force=False,
        data_path='/tmp/unused',
        args=_dry_run_args(),
        process_cmd=None,
        granules=None,
    )


# Criterion 0: Collection ID, Start Time, End Time, BBox still logged in dry-run.
def test_dry_run_subset_logs_subset_parameters(caplog, mocker):
    mocker.patch.object(subsetting.pa, 'find_harmony_runs')
    mocker.patch.object(subsetting.pa, 'subset')
    caplog.set_level(logging.INFO)

    result = _call_dry_run_subset()

    msgs = _messages(caplog)
    assert any(COLLECTION in m and 'Collection ID' in m for m in msgs)
    assert any(START in m and 'Start Time' in m for m in msgs)
    assert any(END in m and 'End Time' in m for m in msgs)
    assert any(BBOX in m and 'BBox' in m for m in msgs)
    assert result == (0, 0)


# Criterion 1: no 'Granules' line showing None; a message states granule
# lookup was not performed in dry-run mode.
def test_dry_run_subset_does_not_log_granules_none(caplog, mocker):
    mocker.patch.object(subsetting.pa, 'find_harmony_runs')
    mocker.patch.object(subsetting.pa, 'subset')
    caplog.set_level(logging.INFO)

    _call_dry_run_subset()

    msgs = _messages(caplog)
    assert not any('Granules:' in m and 'None' in m for m in msgs)
    assert any('granule' in m.lower() and 'dry-run' in m.lower() and 'not performed' in m.lower()
               for m in msgs)


# Criterion 2: run() with --dry-run --subset must not log 'Success Count: 0'
# and must state no downloads or subsets were performed in dry-run mode.
def test_dry_run_run_no_misleading_success_count(caplog, mocker, tmp_path):
    data_dir = str(tmp_path / "data")
    args = pdd.create_parser().parse_args(
        ['-c', 'SOMECOLL', '-d', data_dir, '-sd', START, '-ed', END,
         '-b', BBOX, '--dry-run', '--subset']
    )
    mocker.patch.object(pdd.pa, 'refresh_token', return_value='tok')
    mocker.patch.object(pdd.pa, 'get_cmr_collection_id', return_value=COLLECTION)
    mocker.patch.object(pdd.subsetting, 'is_subsettable', return_value=True)
    mocker.patch.object(pdd.subsetting.pa, 'find_harmony_runs')
    mocker.patch.object(pdd.subsetting.pa, 'subset')
    caplog.set_level(logging.INFO)

    pdd.run(args)

    msgs = _messages(caplog)
    assert not any('Success Count: 0' in m for m in msgs)
    assert any('dry-run' in m.lower() and 'no downloads or subsets' in m.lower() for m in msgs)


# Criterion 3: dry-run output explicitly states Granules and Success Count were
# not performed; subset() still returns (0, 0) without calling pa.subset or
# pa.find_harmony_runs.
def test_dry_run_subset_states_granules_and_success_not_performed(caplog, mocker):
    find_mock = mocker.patch.object(subsetting.pa, 'find_harmony_runs')
    subset_mock = mocker.patch.object(subsetting.pa, 'subset')
    caplog.set_level(logging.INFO)

    result = _call_dry_run_subset()

    msgs = ' '.join(_messages(caplog)).lower()
    assert 'granule' in msgs and 'not performed' in msgs
    assert 'success count' in msgs and 'not performed' in msgs
    assert result == (0, 0)
    find_mock.assert_not_called()
    subset_mock.assert_not_called()
