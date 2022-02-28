#!/usr/bin/env python3
import argparse
import logging
import os
from os import makedirs
from os.path import isdir, basename, join
from urllib.request import urlretrieve
from datetime import datetime, timedelta

from subscriber import podaac_access as pa

__version__ = pa.__version__

LOGLEVEL = os.environ.get('PODAAC_LOGLEVEL', 'WARNING').upper()

logging.basicConfig(level=LOGLEVEL)
logging.debug("Log level set to " + LOGLEVEL)

page_size = 2000

edl = pa.edl
cmr = pa.cmr
token_url = pa.token_url

# The lines below are to get the IP address. You can make this static and
# assign a fixed value to the IPAddr variable


def parse_cycles(cycle_input):
    # if cycle_input is None:
    #     return None
    # if isinstance(cycle_input, list):
    #     return cycle_input
    # return [int(cycle_input)]
    return


def validate(args):
    if args.search_cycles is None and args.startDate is None and args.endDate is None:
        raise ValueError("Error parsing command line arguments: one of [--start-date and --end-date] or [--cycles] are required")  # noqa E501
    if args.search_cycles is not None and args.startDate is not None:
        raise ValueError("Error parsing command line arguments: only one of -sd/--start-date and --cycles are allowed")  # noqa E501
    if args.search_cycles is not None and args.endDate is not None:
        raise ValueError("Error parsing command line arguments: only one of -ed/--end-date and --cycles are allowed")  # noqa E50
    if None in [args.endDate, args.startDate] and args.search_cycles is None:
        raise ValueError("Error parsing command line arguments: Both --start-date and --end-date must be specified")  # noqa E50


def create_parser():
    # Initialize parser
    parser = argparse.ArgumentParser(prog='PO.DAAC bulk-data downloader')

    # Adding Required arguments
    parser.add_argument("-c", "--collection-shortname", dest="collection",required=True, help = "The collection shortname for which you want to retrieve data.")  # noqa E501
    parser.add_argument("-d", "--data-dir", dest="outputDirectory", required=True, help = "The directory where data products will be downloaded.")  # noqa E501

    # Required through validation
    parser.add_argument("--cycle", required=False, dest="search_cycles", help="Cycle number for determining downloads. can be repeated for multiple cycles", action='append', type=int)
    parser.add_argument("-sd", "--start-date", required=False, dest="startDate", help="The ISO date time before which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z")  # noqa E501
    parser.add_argument("-ed", "--end-date", required=False, dest="endDate", help="The ISO date time after which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z")   # noqa E501
    # Adding optional arguments

    # spatiotemporal arguments
    parser.add_argument("-b", "--bounds", dest="bbox", help = "The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b=\"-180,-90,180,90\" syntax when calling from the command line. Default: \"-180,-90,180,90\".", default="-180,-90,180,90")  # noqa E501

    # Arguments for how data are stored locally - much processing is based on
    # the underlying directory structure (e.g. year/Day-of-year)
    parser.add_argument("-dc", dest="cycle", action="store_true", help = "Flag to use cycle number for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dydoy", dest="dydoy", action="store_true", help = "Flag to use start time (Year/DOY) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dymd", dest="dymd", action="store_true", help = "Flag to use start time (Year/Month/Day) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dy", dest="dy", action="store_true", help = "Flag to use start time (Year) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("--offset", dest="offset", help = "Flag used to shift timestamp. Units are in hours, e.g. 10 or -10.")  # noqa E501

    parser.add_argument("-e", "--extensions", dest="extensions", help="The extensions of products to download. Default is [.nc, .h5, .zip, .tar.gz]", default=None, action='append')  # noqa E501
    parser.add_argument("--process", dest="process_cmd", help="Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.", action='append')


    parser.add_argument("--version", action="version", version='%(prog)s ' + __version__, help="Display script version information and exit.")  # noqa E501
    parser.add_argument("--verbose", dest="verbose", action="store_true",help="Verbose mode.")    # noqa E501
    parser.add_argument("-p", "--provider", dest="provider", default='POCLOUD', help="Specify a provider for collection search. Default is POCLOUD.")    # noqa E501

    parser.add_argument("--limit", dest="limit", default='2000', type=int, help="Integer limit for number of granules to download. Useful in testing. Defaults to " + str(page_size))    # noqa E501

    return parser


def run():
    parser = create_parser()
    args = parser.parse_args()

    try:
        pa.validate(args)

        # download specific validations
        # cannot specify all thre options (start, end, cycle)
        # must specify start/end togeher
        # if cycle, then no sd/ed can be given, and vice versa
        validate(args)

    except ValueError as v:
        print(v)
        exit()

    pa.setup_earthdata_login_auth(edl)
    token = pa.get_token(token_url, 'podaac-subscriber', edl)

    provider = args.provider
    start_date_time = args.startDate
    end_date_time = args.endDate
    search_cycles = args.search_cycles
    short_name = args.collection
    extensions = args.extensions
    process_cmd = args.process_cmd
    data_path = args.outputDirectory

    if args.limit is not None:
        page_size = args.limit

    if args.offset:
        ts_shift = timedelta(hours=int(args.offset))

    # Error catching for output directory specifications
    # Must specify -d output path or one time-based output directory flag

    if sum([args.cycle, args.dydoy, args.dymd, args.dy]) > 1:
        parser.error('Too many output directory flags specified, '
                     'Please specify exactly one flag '
                     'from -dc, -dy, -dydoy, or -dymd')

    # This cell will replace the timestamp above with the one read from the `.update` file in the data directory, if it exists.

    if not isdir(data_path):
        print("NOTE: Making new data directory at " + data_path + "(This is the first run.)")
        makedirs(data_path, exist_ok=True)

    # Change this to whatever extent you need. Format is W Longitude,S Latitude,E Longitude,N Latitude
    bounding_extent = args.bbox

    if search_cycles is not None:
        cmr_cycles = search_cycles
        params = [
            ('scroll', "true"),
            ('page_size', page_size),
            ('sort_key', "-start_date"),
            ('provider', provider),
            ('ShortName', short_name),
            ('token', token),
            ('bounding_box', bounding_extent),
        ]
        for v in cmr_cycles:
            params.append(("cycle[]", v))
        if args.verbose:
            print("cycles: " + str(cmr_cycles))

    else:
        temporal_range = pa.get_temporal_range(start_date_time, end_date_time, datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))  # noqa E501
        params = {
            'scroll': "true",
            'page_size': page_size,
            'sort_key': "-start_date",
            'provider': provider,
            'ShortName': short_name,
            'temporal': temporal_range,
            'token': token,
            'bounding_box': bounding_extent,
        }
        if args.verbose:
            print("Temporal Range: " + temporal_range)

    if args.verbose:
        print("Provider: " + provider)

    results = pa.get_search_results(args, params)

    if args.verbose:
        print(str(results['hits'])+" granules found for "+short_name)   # noqa E501

    if any([args.dy, args.dydoy, args.dymd]):
        file_start_times = pa.parse_start_times(results)
    elif args.cycle:
        cycles = pa.parse_cycles(results)

    downloads_all = []
    downloads_data = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "GET DATA" and ('Subtype' not in u or u['Subtype'] != "OPENDAP DATA")] for r in results['items']]
    downloads_metadata = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "EXTENDED METADATA"] for r in results['items']]

    for f in downloads_data:
        downloads_all.append(f)
    for f in downloads_metadata:
        downloads_all.append(f)

    downloads = [item for sublist in downloads_all for item in sublist]

    if len(downloads) >= page_size:
        print("Warning: only the most recent " + str(page_size) + " granules will be downloaded; try adjusting your search criteria (suggestion: reduce time period or spatial region of search) to ensure you retrieve all granules.")

    # filter list based on extension
    if not extensions:
        extensions = pa.extensions
    filtered_downloads = []
    for f in downloads:
        for extension in extensions:
            if f.lower().endswith(extension):
                filtered_downloads.append(f)

    downloads = filtered_downloads

    # https://github.com/podaac/data-subscriber/issues/33
    # Make this a non-verbose message
    # if args.verbose:
    print("Found " + str(len(downloads)) + " total files to download")
    if args.verbose:
        print("Downloading files with extensions: " + str(extensions))

    # NEED TO REFACTOR THIS, A LOT OF STUFF in here
    # Finish by downloading the files to the data directory in a loop.
    # Overwrite `.update` with a new timestamp on success.
    success_cnt = failure_cnt = 0
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
            urlretrieve(f, output_path)
            pa.process_file(process_cmd, output_path, args)
            print(str(datetime.now()) + " SUCCESS: " + f)
            success_cnt = success_cnt + 1
        except Exception as e:
            print(str(datetime.now()) + " FAILURE: " + f)
            failure_cnt = failure_cnt + 1
            print(e)

    print("Downloaded: " + str(success_cnt) + " files\n")
    print("Files Failed to download:" + str(failure_cnt) + "\n")
    pa.delete_token(token_url, token)
    print("END \n\n")
    exit(0)


if __name__ == '__main__':
    run()
