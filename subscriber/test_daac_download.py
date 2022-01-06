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
import json
import logging
import netrc
import os
import socket
from datetime import datetime, timedelta
from http.cookiejar import CookieJar
from os import makedirs
from os.path import isdir, splitext
from urllib import request
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

import boto3
import requests
from botocore.exceptions import ClientError

__version__ = "1.7.0"

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
        raise ValueError(
            "Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")  # noqa E501
    for b in bounds:
        try:
            float(b)
        except ValueError:
            raise ValueError(
                "Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")  # noqa E501

    if args.startDate:
        try:
            datetime.strptime(args.startDate, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError(
                "Error parsing '--start-date' date: " + args.startDate + ". Format must be like 2021-01-14T00:00:00Z")  # noqa E501

    if args.endDate:
        try:
            datetime.strptime(args.endDate, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError(
                "Error parsing '--end-date' date: " + args.endDate + ". Format must be like 2021-01-14T00:00:00Z")  # noqa E501

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


def setup_earthdata_login_auth(endpoint, username, password):
    """
    Set up the request library so that it authenticates against the given
    Earthdata Login endpoint and is able to track cookies between requests.
    This looks in the .netrc file first and if no credentials are found,
    it prompts for them.

    Valid endpoints include:
        urs.earthdata.nasa.gov - Earthdata Login production
    """

    manager = request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, endpoint, username, password)
    auth = request.HTTPBasicAuthHandler(manager)

    jar = CookieJar()
    processor = request.HTTPCookieProcessor(jar)
    opener = request.build_opener(auth, processor)
    opener.addheaders = [('User-agent', 'podaac-subscriber-' + __version__)]
    request.install_opener(opener)


class SessionWithHeaderRedirection(requests.Session):
    """
    Borrowed from https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python
    """

    def __init__(self, username, password):
        super().__init__()
        self.auth = (username, password)

    # Overrides from the library to keep headers when redirected to or from
    # the NASA auth host.
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        url = prepared_request.url

        if 'Authorization' in headers:
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
                    redirect_parsed.hostname != AUTH_HOST and \
                    original_parsed.hostname != AUTH_HOST:
                del headers['Authorization']
        return


###############################################################################
# GET TOKEN FROM CMR
###############################################################################
def get_token(url: str, client_id: str, user_ip: str, endpoint: str) -> str:
    try:
        token: str = ''
        username, _, password = netrc.netrc().authenticators(endpoint)
        xml: str = """<?xml version='1.0' encoding='utf-8'?>
        <token><username>{}</username><password>{}</password><client_id>{}</client_id>
        <user_ip_address>{}</user_ip_address></token>""".format(username, password, client_id, user_ip)  # noqa E501
        headers: Dict = {'Content-Type': 'application/xml', 'Accept': 'application/json'}  # noqa E501
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
        headers: Dict = {'Content-Type': 'application/xml', 'Accept': 'application/json'}  # noqa E501
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
    parser.add_argument("-c", "--collection-shortname", dest="collection", required=True,
                        help="The collection shortname for which you want to retrieve data.")  # noqa E501
    parser.add_argument("-d", "--data-dir", dest="outputDirectory", required=True,
                        help="The directory where data products will be downloaded.")  # noqa E501

    # Adding optional arguments

    # spatiotemporal arguments
    parser.add_argument("-sd", "--start-date", dest="startDate",
                        help="The ISO date time before which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z",
                        default=False)  # noqa E501
    parser.add_argument("-ed", "--end-date", dest="endDate",
                        help="The ISO date time after which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z",
                        default=False)  # noqa E501
    parser.add_argument("-b", "--bounds", dest="bbox",
                        help="The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b=\"-180,-90,180,90\" syntax when calling from the command line. Default: \"-180,-90,180,90\".",
                        default="-180,-90,180,90")  # noqa E501

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
                        help="How far back in time, in minutes, should the script look for data. If running this script as a cron, this value should be equal to or greater than how often your cron runs (default: 60 minutes).",
                        type=int, default=60)  # noqa E501
    parser.add_argument("-e", "--extensions", dest="extensions",
                        help="The extensions of products to download. Default is [.nc, .h5, .zip]", default=None,
                        action='append')  # noqa E501
    parser.add_argument("--process", dest="process_cmd",
                        help="Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.",
                        action='append')

    parser.add_argument("--version", dest="version", action="store_true",
                        help="Display script version information and exit.")  # noqa E501
    parser.add_argument("--verbose", dest="verbose", action="store_true", help="Verbose mode.")  # noqa E501
    parser.add_argument("-p", "--provider", dest="provider", default='POCLOUD',
                        help="Specify a provider for collection search. Default is POCLOUD.")  # noqa E501
    parser.add_argument("-s3", "--s3_bucket", dest="s3_bucket", help="Specify a target s3 bucket to download files to.")
    parser.add_argument("-dm", "--down_mode", dest="download_mode", help="Download mode. valid values: s3 or http.")
    parser.add_argument("-u", "--username", dest="username")
    parser.add_argument("-pw", "--password", dest="password")
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

    username = args.username
    password = args.password

    print("username = " + str(username) + "   edl = " + str(edl))

    setup_earthdata_login_auth(edl, username, password)
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
        print("NOTE: Making new data directory at " + data_path + " (This is the first run.)")
        makedirs(data_path)
    else:
        try:
            with open(data_path + "/.update", "r") as f:
                data_within_last_timestamp = f.read().strip()
        except FileNotFoundError:
            print("WARN: No .update in the data directory. (Is this the first run?)")
        else:
            print(
                "NOTE: .update found in the data directory. (The last run was at " + data_within_last_timestamp + ".)")

    # Change this to whatever extent you need. Format is W Longitude,S Latitude,E Longitude,N Latitude
    bounding_extent = args.bbox

    # There are several ways to query for CMR updates that occured during a given timeframe. Read on in the CMR Search documentation:
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-with-new-granules (Collections)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#c-with-revised-granules (Collections)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#g-production-date (Granules)
    # * https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#g-created-at (Granules)
    # The `created_at` parameter works for our purposes. It's a granule search parameter that returns the records ingested since the input timestamp.

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
        temporal_range = get_temporal_range(start_date_time, end_date_time,
                                            datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))  # noqa E501
        params['temporal'] = temporal_range
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

    download_mode = args.download_mode
    print("Download mode: " + download_mode)

    # Get a new timestamp that represents the UTC time of the search.
    # Then download the records in `umm_json` format for granules
    # that match our search parameters:
    with urlopen(url) as f:
        results = json.loads(f.read().decode())

    if args.verbose:
        print(str(results[
                      'hits']) + " new granules found for " + short_name + " since " + data_within_last_timestamp)  # noqa E501

    if any([args.dy, args.dydoy, args.dymd]):
        try:
            file_start_times = [(r['meta']['native-id'],
                                 datetime.strptime((r['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']),
                                                   "%Y-%m-%dT%H:%M:%S.%fZ")) for r in results['items']]  # noqa E501
        except KeyError:
            raise ValueError('Could not locate start time for data.')
    elif args.cycle:
        try:
            cycles = [(splitext(r['meta']['native-id'])[0],
                       str(r['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Cycle'])) for r in
                      results['items']]  # noqa E501
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
    if (download_mode == 's3'):
        # to get from S3 location
        downloads_data = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "GET DATA VIA DIRECT ACCESS"] for r
                          in results['items']]
    else:
        downloads_data = [[u['URL'] for u in r['umm']['RelatedUrls'] if
                           u['Type'] == "GET DATA" and ('Subtype' not in u or u['Subtype'] != "OPENDAP DATA")] for r in
                          results['items']]

    downloads_metadata = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type'] == "EXTENDED METADATA"] for r in
                          results['items']]

    for f in downloads_data:
        downloads_all.append(f)
    for f in downloads_metadata:
        downloads_all.append(f)

    downloads = [item for sublist in downloads_all for item in sublist]

    if len(downloads) >= page_size:
        print("Warning: only the most recent " + str(
            page_size) + " granules will be downloaded; try adjusting your search criteria (suggestion: reduce time period or spatial region of search) to ensure you retrieve all granules.")

    # filter list based on extension
    if not extensions:
        extensions = [".nc", ".h5", ".zip"]
    filtered_downloads = []
    for f in downloads:
        for extension in extensions:
            if f.lower().endswith(extension):
                filtered_downloads.append(f)

    downloads = filtered_downloads

    if args.verbose:
        print("Found " + str(len(downloads)) + " total files to download")
        print("Downloading files with extensions: " + str(extensions))

    # Finish by downloading the files to the data directory in a loop.
    # Overwrite `.update` with a new timestamp on success.
    success_cnt = failure_cnt = 0

    parsed_url = urlparse("https://urs.earthdata.nasa.gov")
    global AUTH_HOST
    AUTH_HOST = parsed_url.netloc
    session = SessionWithHeaderRedirection(username, password)

    data_url = "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/HLSS30.020/HLS.S30.T53HPV.2021274T004709.v2.0/HLS.S30.T53HPV.2021274T004709.v2.0.B08.tif"
    # data_url = "https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/HLSS30.020/HLS.S30.T55MCN.2021274T004709.v2.0/HLS.S30.T55MCN.2021274T004709.v2.0.B07.tif"
    upload(data_url, session, token, "opera-dev-isl-fwd-hyunlee")

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


def does_product_exist(bucket, key):
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False


def convert_datetime(datetime_obj, strformat="%Y-%m-%dT%H:%M:%S.%fZ"):
    if isinstance(datetime_obj, datetime):
        return datetime_obj.strftime(strformat)
    return datetime.strptime(str(datetime_obj), strformat)


def upload(file_url, session, token, bucket_name, staging_area=None, chunk_size=25600, force_upload=False,
           retry=True):
    """
    This will basically transfer the file contents of the given url to an S3 bucket

    :param dataset: The dataset associated with the given url.
    :param file_url: url to the file.
    :param session: SessionWithHeaderRedirection object.
    :param token: token.
    :param bucket_name: The S3 bucket name to transfer the file url contents to.
    :param staging_area: A staging area where the file url contents will go to. If none, contents will be found
     in the top level of the bucket.
    :param chunk_size: the number of bytes to stream at a time.
    :param force_upload: Set to true to overwrite existing file in s3.
    :param retry: Flag to attempt a retry

    :return:
    """
    file_name = os.path.basename(file_url)

    # For now we put all files for all datsets in same directory. It will be chnaged after ISL lambda update
    # Also it should be in "met_required" directory
    '''
    if staging_area:
        key = os.path.join(staging_area, dataset, file_name)
    else:
        key = os.path.join(dataset, file_name)
    '''

    print("file_name=" + str(file_name))
    # key = os.path.join(staging_area, file_name)
    key = file_name
    print("key = " + str(key))
    upload_start_time = datetime.utcnow()
    headers = {"Echo-Token": token}
    try:
        try:
            if force_upload is False:
                file_exists = does_product_exist(bucket_name, key)
                if file_exists is True:
                    print("SKIP: File exists in S3 already: Bucket=" + str(bucket_name) + " Key= " + str(key))
                    return {}
                else:
                    print("File does NOT exists in S3: Bucket = " + str(bucket_name) + " Key = " + str(key))

            print("before calling session.get url = " + str(file_url))

            # this part is from pcm_commons.upload_utils
            # getting error with FileNotFound???
            #with session.get(file_url, headers=headers, stream=True) as r:
            #    print("r.status_code = " + str(r.status_code))
            #    if r.status_code != 200:
            #        r.raise_for_status()
            #logger.info("Uploading {} to Bucket={}, Key={}".format(file_name, bucket_name, key))
            #    total_bytes = 0
            #    with open("s3://{}/{}".format(bucket_name, key), "wb") as out:
            #        for chunk in r.iter_content(chunk_size=chunk_size):
            #            out.write(chunk)
            #            total_bytes += len(chunk)
            #for chunk in r.iter_content(chunk_size=chunk_size):
            #logger.debug("Uploading {} byte(s)".format(len(chunk)))
            #print("Uploading {} byte(s)".format(len(chunk)))
            #out.write(chunk)
            #    bucket.put(Body=chunk)
            #    total_bytes += len(chunk)
            return upload_stats
        except ConnectionResetError as ce:
            raise Exception(str(ce))
        except requests.exceptions.HTTPError as he:
            raise Exception(str(he))
    except Exception as e:
        if retry is True:
            return upload(file_url, session, token, bucket_name,
                          staging_area=staging_area, chunk_size=chunk_size, retry=False)
        else:
            return {"failed_download": {file_url}}


if __name__ == '__main__':
    run()
