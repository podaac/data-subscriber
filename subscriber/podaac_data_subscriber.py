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


from urllib import request
from http.cookiejar import CookieJar
import netrc
import requests
import json
import socket
import argparse
import logging
import os
from os import makedirs
from os.path import isdir, basename, join, splitext
import subprocess
from urllib.parse import urlencode
from urllib.request import urlopen, urlretrieve
from datetime import datetime, timedelta

__version__ = "1.7.2"

LOGLEVEL = os.environ.get('SUBSCRIBER_LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)
logging.debug("Log level set to " + LOGLEVEL)

page_size = 2000

edl = "urs.earthdata.nasa.gov"
cmr = "cmr.earthdata.nasa.gov"
token_url = "https://" + cmr + "/legacy-services/rest/tokens"

def get_temporal_range(start, end, now):
    start = start if start is not False else None
    end = end if end is not False else None

    if start is not None and end is not None:
        return "{},{}".format(start, end)
    if start is not None and end is None:
        return "{},{}".format(start, now)
    if start is None and end is not None:
        return "1900-01-01T00:00:00Z,{}".format(end)

    raise ValueError("One of start-date or end-date must be specified.")


def validate(args):
    bounds = args.bbox.split(',')
    if len(bounds) != 4:
        raise ValueError("Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")   # noqa E501
    for b in bounds:
        try:
            float(b)
        except ValueError:
            raise ValueError("Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")   # noqa E501

    if args.startDate:
        try:
            datetime.strptime(args.startDate, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError("Error parsing '--start-date' date: " + args.startDate + ". Format must be like 2021-01-14T00:00:00Z")   # noqa E501

    if args.endDate:
        try:
            datetime.strptime(args.endDate, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError("Error parsing '--end-date' date: " + args.endDate + ". Format must be like 2021-01-14T00:00:00Z")  # noqa E501

    if args.minutes:
        try:
            int(args.minutes)
        except ValueError:
            raise ValueError("Error parsing '--minutes': " + args.minutes + ". Number must be an integer.")  # noqa E501


# The lines below are to get the IP address. You can make this static and
# assign a fixed value to the IPAddr variable
hostname = socket.gethostname()
IPAddr = "127.0.0.1"  # socket.gethostbyname(hostname)


# ## Authentication setup
#
# The function below will allow Python scripts to log into any Earthdata Login
#  application programmatically.  To avoid being prompted for
# credentials every time you run and also allow clients such as curl to log in,
#  you can add the following to a `.netrc` (`_netrc` on Windows) file in
#  your home directory:
#
# ```
# machine urs.earthdata.nasa.gov
#     login <your username>
#     password <your password>
# ```
#
# Make sure that this file is only readable by the current user
# or you will receive an error stating
# "netrc access too permissive."
#
# `$ chmod 0600 ~/.netrc`
#
# You'll need to authenticate using the netrc method when running from
# command line with [`papermill`](https://papermill.readthedocs.io/en/latest/).
# You can log in manually by executing the cell below when running in the
# notebook client in your browser.*


def setup_earthdata_login_auth(endpoint):
    """
    Set up the request library so that it authenticates against the given
    Earthdata Login endpoint and is able to track cookies between requests.
    This looks in the .netrc file first and if no credentials are found,
    it prompts for them.

    Valid endpoints include:
        urs.earthdata.nasa.gov - Earthdata Login production
    """
    try:
        username, _, password = netrc.netrc().authenticators(endpoint)
    except (FileNotFoundError, TypeError):
        # FileNotFound = There's no .netrc file
        # TypeError = The endpoint isn't in the netrc file,
        #  causing the above to try unpacking None
        print("There's no .netrc file or the The endpoint isn't in the netrc file")  # noqa E501

    manager = request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, endpoint, username, password)
    auth = request.HTTPBasicAuthHandler(manager)

    jar = CookieJar()
    processor = request.HTTPCookieProcessor(jar)
    opener = request.build_opener(auth, processor)
    opener.addheaders = [('User-agent', 'podaac-subscriber-' + __version__)]
    request.install_opener(opener)


###############################################################################
# GET TOKEN FROM CMR
###############################################################################
def get_token(url: str, client_id: str, user_ip: str, endpoint: str) -> str:
    try:
        token: str = ''
        username, _, password = netrc.netrc().authenticators(endpoint)
        xml: str = """<?xml version='1.0' encoding='utf-8'?>
        <token><username>{}</username><password>{}</password><client_id>{}</client_id>
        <user_ip_address>{}</user_ip_address></token>""".format(username, password, client_id, user_ip)   # noqa E501
        headers: Dict = {'Content-Type': 'application/xml', 'Accept': 'application/json'}   # noqa E501
        resp = requests.post(url, headers=headers, data=xml)
        response_content: Dict = json.loads(resp.content)
        token = response_content['token']['id']

    # What error is thrown here? Value Error? Request Errors?
    except:  # noqa E722
        print("Error getting the token - check user name and password")
    return token


###############################################################################
# DELETE TOKEN FROM CMR
###############################################################################
def delete_token(url: str, token: str) -> None:
    try:
        headers: Dict = {'Content-Type': 'application/xml','Accept': 'application/json'}   # noqa E501
        url = '{}/{}'.format(url, token)
        resp = requests.request('DELETE', url, headers=headers)
        if resp.status_code == 204:
            print("CMR token successfully deleted")
        else:
            print("CMR token deleting failed.")
    except:  # noqa E722
        print("Error deleting the token")
    exit(0)


def create_parser():
    # Initialize parser
    parser = argparse.ArgumentParser()

    # Adding Required arguments
    parser.add_argument("-c", "--collection-shortname", dest="collection",required=True, help = "The collection shortname for which you want to retrieve data.")  # noqa E501
    parser.add_argument("-d", "--data-dir", dest="outputDirectory", required=True, help = "The directory where data products will be downloaded.")  # noqa E501

    # Adding optional arguments

    # spatiotemporal arguments
    parser.add_argument("-sd", "--start-date", dest="startDate", help = "The ISO date time before which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z", default=False)  # noqa E501
    parser.add_argument("-ed", "--end-date", dest="endDate", help = "The ISO date time after which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z", default=False)   # noqa E501
    parser.add_argument("-b", "--bounds", dest="bbox", help = "The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b=\"-180,-90,180,90\" syntax when calling from the command line. Default: \"-180,-90,180,90\".", default="-180,-90,180,90")  # noqa E501

    # Arguments for how data are stored locally - much processing is based on
    # the underlying directory structure (e.g. year/Day-of-year)
    parser.add_argument("-dc", dest="cycle", action="store_true", help = "Flag to use cycle number for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dydoy", dest="dydoy", action="store_true", help = "Flag to use start time (Year/DOY) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dymd", dest="dymd", action="store_true", help = "Flag to use start time (Year/Month/Day) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("-dy", dest="dy", action="store_true", help = "Flag to use start time (Year) of downloaded data for directory where data products will be downloaded.")  # noqa E501
    parser.add_argument("--offset", dest="offset", help = "Flag used to shift timestamp. Units are in hours, e.g. 10 or -10.")  # noqa E501

    parser.add_argument("-m", "--minutes", dest="minutes", help = "How far back in time, in minutes, should the script look for data. If running this script as a cron, this value should be equal to or greater than how often your cron runs (default: 60 minutes).", type=int, default=60)  # noqa E501
    parser.add_argument("-e", "--extensions", dest="extensions", help = "The extensions of products to download. Default is [.nc, .h5, .zip]", default=None, action='append')  # noqa E501
    parser.add_argument("--process", dest="process_cmd", help = "Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.", action='append')


    parser.add_argument("--version", dest="version", action="store_true",help="Display script version information and exit.")  # noqa E501
    parser.add_argument("--verbose", dest="verbose", action="store_true",help="Verbose mode.")    # noqa E501
    parser.add_argument("-p", "--provider", dest="provider", default='POCLOUD', help="Specify a provider for collection search. Default is POCLOUD.")    # noqa E501
    return parser


def run():
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        print("PO.DAAC Data Subscriber v" + __version__)
        exit()
    try:
        validate(args)
    except ValueError as v:
        print(v)
        exit()

    setup_earthdata_login_auth(edl)
    token = get_token(token_url, 'podaac-subscriber', IPAddr, edl)
    mins = args.minutes  # In this case download files ingested in the last 60 minutes -- change this to whatever setting is needed

    defined_time_range = False

    provider = args.provider

    start_date_time = args.startDate
    end_date_time = args.endDate

    if start_date_time or end_date_time:
        defined_time_range = True

    short_name = args.collection
    extensions = args.extensions
    process_cmd = args.process_cmd

    data_path = args.outputDirectory
    # You should change `data_path` to a suitable download path on your file system.

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
    #

    # This is the default way of finding data if no other
    if defined_time_range:
        data_within_last_timestamp = start_date_time
    else:
        data_within_last_timestamp = (datetime.utcnow() - timedelta(minutes=mins)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # This cell will replace the timestamp above with the one read from the `.update` file in the data directory, if it exists.

    if not isdir(data_path):
        print("NOTE: Making new data directory at " + data_path + "(This is the first run.)")
        makedirs(data_path)
    else:
        try:
            with open(data_path + "/.update", "r") as f:
                data_within_last_timestamp = f.read().strip()
        except FileNotFoundError:
            print("WARN: No .update in the data directory. (Is this the first run?)")
        else:
            print("NOTE: .update found in the data directory. (The last run was at " + data_within_last_timestamp + ".)")

    # Change this to whatever extent you need. Format is W Longitude,S Latitude,E Longitude,N Latitude
    bounding_extent = args.bbox

    # There are several ways to query for CMR updates that occured during a given timeframe. Read on in the CMR Search documentation:
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-with-new-granules (Collections)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-with-revised-granules (Collections)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#g-production-date (Granules)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#g-created-at (Granules)
    # The `created_at` parameter works for our purposes. It's a granule search parameter that returns the records ingested since the input timestamp.

    if defined_time_range:
        # if(data_since):
        temporal_range = get_temporal_range(start_date_time, end_date_time, datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))  # noqa E501

    params = {
        'scroll': "true",
        'page_size': page_size,
        'sort_key': "-start_date",
        'provider': provider,
        'ShortName': short_name,
        'updated_since': data_within_last_timestamp,
        'token': token,
        'bounding_box': bounding_extent,
    }

    if defined_time_range:
        params = {
            'scroll': "true",
            'page_size': page_size,
            'sort_key': "-start_date",
            'provider': provider,
            'updated_since': data_within_last_timestamp,
            'ShortName': short_name,
            'temporal': temporal_range,
            'token': token,
            'bounding_box': bounding_extent,
        }

        if args.verbose:
            print("Temporal Range: " + temporal_range)

    if args.verbose:
        print("Provider: " + provider)
        print("Updated Since: " + data_within_last_timestamp)

    # Get the query parameters as a string and then the complete search url:
    query = urlencode(params)
    url = "https://" + cmr + "/search/granules.umm_json?" + query
    if args.verbose:
        print(url)

    # Get a new timestamp that represents the UTC time of the search.
    # Then download the records in `umm_json` format for granules
    # that match our search parameters:
    with urlopen(url) as f:
        results = json.loads(f.read().decode())

    if args.verbose:
        print(str(results['hits'])+" new granules found for "+short_name+" since "+data_within_last_timestamp)   # noqa E501

    if any([args.dy, args.dydoy, args.dymd]):
        try:
            file_start_times = [(r['meta']['native-id'], datetime.strptime((r['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']), "%Y-%m-%dT%H:%M:%S.%fZ")) for r in results['items']]  # noqa E501
        except KeyError:
            raise ValueError('Could not locate start time for data.')
    elif args.cycle:
        try:
            cycles = [(splitext(r['meta']['native-id'])[0],str(r['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Cycle'])) for r in results['items']]  # noqa E501
        except KeyError:
            parser.error('No cycles found within collection granules. '
                         'Specify an output directory or '
                         'choose another output directory flag other than -dc.')  # noqa E501


    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Neatly print the first granule record (if one was returned):
    # if len(results['items'])>0:
    #    print(dumps(results['items'][0], indent=2))

    # The link for http access can be retrieved from each granule
    # record's `RelatedUrls` field.
    # The download link is identified by `"Type": "GET DATA"` but there are
    # other data files in EXTENDED METADATA" field.
    # Select the download URL for each of the granule records:

    downloads_all = []
    downloads_data = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "GET DATA" and ('Subtype' not in u or u['Subtype'] != "OPENDAP DATA")] for r in results['items']]

    downloads_metadata = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "EXTENDED METADATA"] for r in results['items']]

    for f in downloads_data:
        downloads_all.append(f)
    for f in downloads_metadata:
        downloads_all.append(f)

    downloads = [item for sublist in downloads_all for item in sublist]

    if len(downloads) >= page_size:
        print("Warning: only the most recent "+ str(page_size) + " granules will be downloaded; try adjusting your search criteria (suggestion: reduce time period or spatial region of search) to ensure you retrieve all granules.")


    #filter list based on extension
    if not extensions:
        extensions = [".nc", ".h5", ".zip"]
    filtered_downloads = []
    for f in downloads:
        for extension in extensions:
            if f.lower().endswith(extension):
                filtered_downloads.append(f)

    downloads = filtered_downloads

    # https://github.com/podaac/data-subscriber/issues/33
    # Make this a non-verbose message
    #if args.verbose:
    print("Found " + str(len(downloads)) + " total files to download")
    if args.verbose:
        print("Downloading files with extensions: " + str(extensions))


    # Finish by downloading the files to the data directory in a loop.
    # Overwrite `.update` with a new timestamp on success.
    success_cnt = failure_cnt = 0

    def check_dir(path):
        if not isdir(path):
            makedirs(path)

    def prepare_time_output(times, prefix, file):
        """"
        Create output directory using using:
            OUTPUT_DIR/YEAR/DAY_OF_YEAR/
            OUTPUT_DIR/YEAR/MONTH/DAY
            OUTPUT_DIR/YEAR
        .update stored in OUTPUT_DIR/

        Parameters
        ----------
        times : list
            list of tuples consisting of granule names and start times
        prefix : string
            prefix for output path, either custom output -d or short name
        file : string
            granule file name

        Returns
        -------
        write_path
            string path to where granules will be written
        """

        time_match = [dt for dt in
                      times if dt[0] == splitext(basename(file))[0]]

        # Found on 11/11/21
        # https://github.com/podaac/data-subscriber/issues/28
        # if we don't find the time match array, try again using the
        # filename AND its suffix (above removes it...)
        if len(time_match) == 0:
            time_match = [dt for dt in
                          times if dt[0] == basename(file)]
        time_match = time_match[0][1]

        # offset timestamp for output paths
        if args.offset:
            time_match = time_match + ts_shift

        year = time_match.strftime('%Y')
        month = time_match.strftime('%m')
        day = time_match.strftime('%d')
        day_of_year = time_match.strftime('%j')

        if args.dydoy:
            time_dir = join(year, day_of_year)
        elif args.dymd:
            time_dir = join(year, month, day)
        elif args.dy:
            time_dir = year
        else:
            raise ValueError('Temporal output flag not recognized.')
        check_dir(join(prefix, time_dir))
        write_path = join(prefix, time_dir, basename(file))
        return write_path

    def prepare_cycles_output(data_cycles, prefix, file):
        """"
        Create output directory using OUTPUT_DIR/CYCLE_NUMBER
        .update stored in OUTPUT_DIR/

        Parameters
        ----------
        data_cycles : list
            list of tuples consisting of granule names and cycle numbers
            prefix : string
            prefix for output path, either custom output -d or short name
        file : string
            granule file name

        Returns
        -------
        write_path : string
            string path to where granules will be written
        """
        cycle_match = [
            cycle for cycle in data_cycles if cycle[0] == splitext(basename(file))[0]
        ][0]
        cycle_dir = "c" + cycle_match[1].zfill(4)
        check_dir(join(prefix, cycle_dir))
        write_path = join(prefix, cycle_dir, basename(file))
        return write_path

    def process_file(output_path):
        if not process_cmd:
            return
        else:
            for cmd in process_cmd:
                if args.verbose:
                    print(f'Running: {cmd} {output_path}')
                subprocess.run(cmd.split() + [output_path],
                               check=True)

    for f in downloads:
        try:
            for extension in extensions:
                if f.lower().endswith(extension):
                    # -d flag, args.outputDirectory
                    output_path = join(data_path, basename(f))
                    # -dy, args.dy, -dydoy, args.dydoy and -dymd, args.dymd
                    if any([args.dy, args.dydoy, args.dymd]):
                        output_path = prepare_time_output(
                            file_start_times, data_path, f)
                    # -dc flag
                    if args.cycle:
                        output_path = prepare_cycles_output(
                            cycles, data_path, f)
                    urlretrieve(f, output_path)
                    process_file(output_path)
                    print(str(datetime.now()) + " SUCCESS: " + f)
                    success_cnt = success_cnt + 1
        except Exception as e:
            print(str(datetime.now()) + " FAILURE: " + f)
            failure_cnt = failure_cnt + 1
            print(e)

    # If there were updates to the local time series during this run and no
    # exceptions were raised during the download loop, then overwrite the
    #  timestamp file that tracks updates to the data folder
    #   (`resources/nrt/.update`):
    if len(results['items']) > 0:
        if not failure_cnt > 0:
            with open(data_path + "/.update", "w") as f:
                f.write(timestamp)

    print("Downloaded: " + str(success_cnt) + " files\n")
    print("Files Failed to download:" + str(failure_cnt) + "\n")
    delete_token(token_url, token)
    print("END \n\n")


if __name__ == '__main__':
    run()
