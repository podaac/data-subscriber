#!/usr/bin/env python3

# # Access Sentinel-6 MF Data using a script
# This script shows a simple way to maintain a local time series of Sentinel-6
# data using the
# [CMR Search API]
# (https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
# It downloads granules the ingested since
#   the previous run to a designated data
#   folder and overwrites a hidden file inside with the timestamp of the
# CMR Search request on success.
# Before you beginning this tutorial, make sure you have an Earthdata account:
# [https://urs.earthdata.nasa.gov] .
# Accounts are free to create and take just a moment to set up.
import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from os import makedirs
from os.path import isdir, basename, join, isfile, exists
from urllib.error import HTTPError

from subscriber import podaac_access as pa
from subscriber import subsetting
from subscriber import token_formatter

__version__ = pa.__version__

page_size = 2000

edl = pa.edl
cmr = pa.cmr
token_url = pa.token_url


def get_update_file(data_dir, collection_name):
    if isfile(data_dir + "/.update__" + collection_name):
        return data_dir + "/.update__" + collection_name
    elif isfile(data_dir + "/.update"):
        logging.warning(
            "found a deprecated use of '.update' file at {0}. After this run it will be renamed to {1}".format(
                data_dir + "/.update", data_dir + "/.update__" + collection_name))
        return data_dir + "/.update"

    return None


def validate(args):
    if args.minutes is None and args.startDate is False and args.endDate is False:
        raise ValueError(
            "Error parsing command line arguments: one of --start-date, --end-date or --minutes are required")


def create_parser():
    # Initialize parser
    parser = argparse.ArgumentParser(prog='PO.DAAC data subscriber')

    # Adding Required arguments
    parser.add_argument("-c", "--collection-shortname", dest="collection", required=True,
                        help="The collection shortname for which you want to retrieve data.")  # noqa E501
    parser.add_argument("-d", "--data-dir", dest="outputDirectory", required=True,
                        help="The directory where data products will be downloaded.")  # noqa E501

    # Adding optional arguments
    parser.add_argument("-f", "--force", dest="force", action="store_true", help = "Flag to force downloading files that are listed in CMR query, even if the file exists and checksum matches")  # noqa E501

    # spatiotemporal arguments
    parser.add_argument("-sd", "--start-date", dest="startDate",
                        help="The ISO date time after which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z",
                        default=False)  # noqa E501
    parser.add_argument("-ed", "--end-date", dest="endDate",
                        help="The ISO date time before which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z",
                        default=False)  # noqa E501
    parser.add_argument("-b", "--bounds", dest="bbox",
                        help="The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b=\"-180,-90,180,90\" syntax when calling from the command line. Default: \"-180,-90,180,90\".",
                        default=None)  # noqa E501

    # Arguments for how data are stored locally - much processing is based on
    # the underlying directory structure (e.g. year/Day-of-year)
    parser.add_argument("-dc", dest="cycle", action="store_true",
                        help="Flag to use cycle number for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dydoy", dest="dydoy", action="store_true",
                        help="Flag to use start time (Year/DOY) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dymd", dest="dymd", action="store_true",
                        help="Flag to use start time (Year/Month/Day) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dy", dest="dy", action="store_true",
                        help="Flag to use start time (Year) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("--offset", dest="offset",
                        help="Flag used to shift timestamp. Units are in hours, e.g. 10 or -10.")  # noqa E501

    parser.add_argument("-m", "--minutes", dest="minutes",
                        help="How far back in time, in minutes, should the script look for data. If running this script as a cron, this value should be equal to or greater than how often your cron runs.",
                        type=int, default=None)  # noqa E501
    parser.add_argument("-e", "--extensions", dest="extensions",
                        help="Regexps of extensions of products to download. Default is [.nc, .h5, .zip, .tar.gz, .tiff]", default=None,
                        action='append')  # noqa E501
    parser.add_argument("--process", dest="process_cmd",
                        help="Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.",
                        action='append')

    parser.add_argument("--version", action="version", version='%(prog)s ' + __version__,
                        help="Display script version information and exit.")  # noqa E501
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Verbose mode.")  # noqa E501

    parser.add_argument("-p", "--provider", dest="provider", default='POCLOUD',
                        help="Specify a provider for collection search. Default is POCLOUD.")  # noqa E501
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Search and identify files to download, but do not actually download them")  # noqa E501
    parser.add_argument("--subset", dest="subset", action="store_true", help="Subset the data via Harmony calls.")  # noqa E501

    return parser



def run(args=None):
    if args is None:
        parser = create_parser()
        args = parser.parse_args()


    try:
        pa.validate(args)
        validate(args)
    except ValueError as v:
        logging.error(str(v))
        exit(1)

    pa.setup_earthdata_login_auth(edl)
    token = pa.get_token(token_url)

    mins = args.minutes  # In this case download files ingested in the last 60 minutes -- change this to whatever setting is needed
    provider = args.provider
    start_date_time = args.startDate
    end_date_time = args.endDate
    short_name = args.collection
    extensions = args.extensions
    process_cmd = args.process_cmd
    data_path = args.outputDirectory

    defined_time_range = False
    if start_date_time or end_date_time:
        defined_time_range = True

    ts_shift = 0
    if args.offset:
        ts_shift = timedelta(hours=int(args.offset))

    # Error catching for output directory specifications
    # Must specify -d output path or one time-based output directory flag

    if sum([args.cycle, args.dydoy, args.dymd, args.dy]) > 1:
        parser.error('Too many output directory flags specified, '
                     'Please specify exactly one flag '
                     'from -dc, -dy, -dydoy, or -dymd')

    # **The search retrieves granules ingested during the last `n` minutes.
    # ** A file in your local data dir  file that tracks updates to your data directory,
    # if one file exists.

    # This is the default way of finding data if no other
    if defined_time_range:
        data_within_last_timestamp = start_date_time if start_date_time else end_date_time
    else:
        data_within_last_timestamp = (datetime.utcnow() - timedelta(minutes=mins)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # This cell will replace the timestamp above with the one read from the `.update` file in the data directory, if it exists.

    if not isdir(data_path):
        logging.info("NOTE: Making new data directory at " + data_path + "(This is the first run.)")
        makedirs(data_path, exist_ok=True)

    else:
        update_file = get_update_file(data_path, short_name)
        if update_file is not None:
            try:
                with open(update_file, "r") as f:
                    data_within_last_timestamp = f.read().strip()
                    logging.info(
                        "NOTE: Update found in the data directory. (The last run was at " + data_within_last_timestamp + ".)")
            except FileNotFoundError:
                logging.warning("No .update in the data directory. (Is this the first run?)")
        else:
            logging.warning("No .update__" + short_name + " in the data directory. (Is this the first run?)")

    if defined_time_range:
        # if(data_since):
        temporal_range = pa.get_temporal_range(start_date_time, end_date_time,
                                               datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))  # noqa E501

    params = [
        ('page_size',page_size),
        ('sort_key', "-start_date"),
        ('provider', provider),
        ('ShortName', short_name),
        ('updated_since', data_within_last_timestamp),
        ('token', token),
    ]

    if defined_time_range:
        params = [
            ('page_size', page_size),
            ('sort_key', "-start_date"),
            ('provider', provider),
            ('updated_since', data_within_last_timestamp),
            ('ShortName', short_name),
            ('temporal', temporal_range),
            ('token', token),
        ]
        if args.verbose:
            logging.info("Temporal Range: " + temporal_range)

    if args.bbox is not None:
        params.append(('bounding_box', args.bbox))

    if args.verbose:
        logging.info("Provider: " + provider)
        logging.info("Updated Since: " + data_within_last_timestamp)

    # If 401 is raised, refresh token and try one more time
    try:
        results = pa.get_search_results(params, args.verbose)
    except HTTPError as e:
        if e.code == 401:
            token = pa.refresh_token(token)
            # Updated: This is not always a dictionary...
            # in fact, here it's always a list of tuples
            for  i, p in enumerate(params) :
                if p[1] == "token":
                    params[i] = ("token", token)
            #params['token'] = token
            results = pa.get_search_results(params, args.verbose)
        else:
            raise e

    if args.verbose:
        logging.info(str(results[
                             'hits']) + " new granules found for " + short_name + " since " + data_within_last_timestamp)  # noqa E501

    file_start_times = None
    cycles = None
    if any([args.dy, args.dydoy, args.dymd]):
        file_start_times = pa.parse_start_times(results)
    elif args.cycle:
        cycles = pa.parse_cycles(results)

    granules = results['items']
    granules = list(map(lambda granule: granule['meta']['concept-id'], granules))

    collection_id = pa.get_cmr_collection_id(
        collection_short_name=args.collection,
        provider=args.provider,
        token=token,
        verbose=args.verbose
    )

    subsettable = False
    if args.subset:
        subsettable = subsetting.is_subsettable(
            collection_id=collection_id,
            token=token,
        )

    if subsettable:
        success_cnt, failure_cnt = subsetting.subset(
            collection_id=collection_id,
            start_date_time=args.startDate,
            end_date_time=args.endDate,
            bbox=args.bbox,
            force=args.force,
            data_path=data_path,
            args=args,
            process_cmd=process_cmd,
            granules=granules
        )
    else:
        success_cnt, failure_cnt, skip_cnt = cmr_downloader(
            granules=results['items'],
            extensions=extensions,
            args=args,
            data_path=data_path,
            file_start_times=file_start_times,
            ts_shift=ts_shift,
            cycles=cycles,
            process_cmd=process_cmd
        )

    if len(granules) > 0 and not args.dry_run:
        if not failure_cnt > 0:
            with open(f'{data_path}/.update__{args.collection}', 'w') as f:
                f.write(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    if success_cnt > 0:
        try:
            pa.create_citation_file(short_name, provider, data_path, token, args.verbose)
        except:
            logging.debug('Error generating citation', exc_info=True)

    logging.info('END\n\n')


def cmr_downloader(granules, extensions, args, data_path, file_start_times, ts_shift, cycles, process_cmd):
    downloads_all = []

    downloads_data = [
        [
            u['URL'] for u in r['umm']['RelatedUrls']
            if u['Type'] == "GET DATA"
               and ('Subtype' not in u or u['Subtype'] != 'OPENDAP DATA')
        ] for r in granules
    ]
    downloads_metadata = [
        [
            u['URL'] for u in r['umm']['RelatedUrls']
            if u['Type'] == 'EXTENDED METADATA'
        ] for r in granules
    ]
    checksums = pa.extract_checksums(granules)

    for f in downloads_data:
        downloads_all.append(f)
    for f in downloads_metadata:
        downloads_all.append(f)

    downloads = [item for sublist in downloads_all for item in sublist]

    # filter list based on extension
    if not extensions:
        extensions = pa.extensions
    filtered_downloads = []
    for f in downloads:
        for extension in extensions:
            if pa.search_extension(extension, f):
                filtered_downloads.append(f)

    downloads = filtered_downloads

    # https://github.com/podaac/data-subscriber/issues/33
    # Make this a non-verbose message
    # if args.verbose:
    logging.info("Found " + str(len(downloads)) + " total files to download")
    if args.verbose:
        logging.info("Downloading files with extensions: " + str(extensions))

    if args.dry_run:
        logging.info("Dry-run option specified. Listing Downloads.")
        for download in downloads:
            logging.info(download)
        logging.info("Dry-run option specific. Exiting.")
        return 0, 0, 0

    # NEED TO REFACTOR THIS, A LOT OF STUFF in here
    # Finish by downloading the files to the data directory in a loop.
    # Overwrite `.update` with a new timestamp on success.
    success_cnt = failure_cnt = skip_cnt = 0
    for f in downloads:
        try:
            # -d flag, args.outputDirectory
            output_path = join(data_path, basename(f))
            # -dy, args.dy, -dydoy, args.dydoy and -dymd, args.dymd
            if any([args.dy, args.dydoy, args.dymd]):
                output_path = pa.prepare_time_output(
                    file_start_times, data_path, f, args, ts_shift)
            # -dc flag
            if args.cycle:
                output_path = pa.prepare_cycles_output(
                    cycles, data_path, f)

            # decide if we should actually download this file (e.g. we may already have the latest version)
            if (exists(output_path) and not args.force and pa.checksum_does_match(
                    output_path, checksums)):
                logging.info(str(datetime.now()) + " SKIPPED: " + f)
                skip_cnt += 1
                continue

            pa.download_file(f, output_path)
            pa.process_file(process_cmd, output_path, args)
            logging.info(str(datetime.now()) + " SUCCESS: " + f)
            success_cnt = success_cnt + 1
        except Exception:
            logging.warning(str(datetime.now()) + " FAILURE: " + f, exc_info=True)
            failure_cnt = failure_cnt + 1

    logging.info("Downloaded Files: " + str(success_cnt))
    logging.info("Failed Files:     " + str(failure_cnt))
    logging.info("Skipped Files:    " + str(skip_cnt))

    return success_cnt, failure_cnt, skip_cnt

def main():
    log_format = '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
    log_level = os.environ.get('PODAAC_LOGLEVEL', 'INFO').upper()
    logging.basicConfig(stream=sys.stdout,
                        format=log_format,
                        level=log_level)
    for handler in logging.root.handlers:
        handler.setFormatter(token_formatter.TokenFormatter(log_format))
    logging.debug("Log level set to " + log_level)

    try:
        run()
    except Exception as e:
        logging.exception("Uncaught exception occurred during execution.")
        exit(hash(e))


if __name__ == '__main__':
    pa.check_for_latest()
    main()
