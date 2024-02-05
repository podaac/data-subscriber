import logging
from subscriber import podaac_access as pa


def is_subsettable(collection_id, token):
    """
    Query CMR to determine if the provided collection is subsettable by
    Harmony. In order to be subsettable, an appropriate UMM-S association
    needs to be in place.

    Parameters
    ----------
    collection_id: str
        The CMR collection ID
    token: str
        EDL token used to query CMR

    Returns
    -------
    bool
        True if the collection is Harmony subsettable. False if the
        collection is not Harmony subsettable.
    """
    subsettable = pa.is_collection_harmony_subsettable(collection_id, token)
    if not subsettable:
        logging.info('Collection is not harmony subsettable, proceeding with traditional download')
    return subsettable


def subset(collection_id, start_date_time, end_date_time, bbox, force, data_path, args,
           process_cmd, granules=None):
    """
    Submit Harmony subsetting request and download the results

    Parameters
    ----------
    collection_id: str
        The CMR collection ID to Harmony subset
    start_date_time: str
        ISO formatted start time. Used to subset granules in collection
    end_date_time: str
        ISO formatted end time. Used to subset granules in collection
    bbox: str
        String in format W,S,E,N
    force: bool
        If true, overwrite files on download of results
    data_path: str
        Local path to where results should be downloaded
    args: argparse.Namespace
        Script args
    process_cmd: str
        Command to run on each granule upon successful download
    granules: list, optional
        List of granules to pass to Harmony. This is optional -- if not
        provided, Harmony will use the provided spatiotemporal bounds to
        find overlapping granules. If provided, Harmony will only operate
        on the provided granules.

    Returns
    -------
    tuple
        (files downloaded successfully, files failed)
    """
    if args.dry_run:
        logging.info('Dry-run option specified. Listing Harmony subsetting parameters.')
        logging.info(f'\tCollection ID: {collection_id}')
        logging.info(f'\tStart Time:    {start_date_time}')
        logging.info(f'\tEnd Time:      {end_date_time}')
        logging.info(f'\tBBox:          {bbox}')
        logging.info(f'\tGranules:      {granules}')
        return 0, 0

    job_id = pa.find_harmony_runs(
        collection=collection_id,
        bbox=bbox,
        starttime=start_date_time,
        endtime=end_date_time,
        output_dir=data_path,
        granules=granules
    )
    if not job_id:
        job_id = pa.subset(
            concept_id=collection_id,
            bbox=bbox,
            start_time=start_date_time,
            stop_time=end_date_time,
            granules=granules,
            verbose=args.verbose
        )
        pa.save_harmony_run(
            collection=collection_id,
            bbox=bbox,
            starttime=start_date_time,
            endtime=end_date_time,
            job_id=job_id,
            output_dir=data_path,
            granule_ids=granules
        )
    else:
        logging.info('Resuming existing harmony job id...')

    logging.info('Waiting for Harmony subsetting job to complete...')
    job_status = pa.download_subsetted_files(job_id, data_path, args, force, process_cmd)
    return 1, 1 if job_status in ('complete_with_errors', 'failed') else 0
