import json
import logging
import netrc
import re
from http.cookiejar import CookieJar
import os
from os import makedirs
from os.path import isdir, basename, join, splitext, isfile
from typing import Dict
from urllib import request
from urllib.error import HTTPError
from urllib.request import urlretrieve
import subprocess
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import hashlib
import time
from requests.auth import HTTPBasicAuth
import harmony
import concurrent.futures
from dateutil.parser import *
import functools
from packaging import version

import requests
import tenacity
from datetime import datetime

__version__ = "1.15.0"
extensions = ["\\.nc", "\\.h5", "\\.zip", "\\.tar.gz", "\\.tiff"]
edl = "urs.earthdata.nasa.gov"
cmr = "cmr.earthdata.nasa.gov"
graph = "graphql.earthdata.nasa.gov"
graph_url = "https://"+graph+"/api"
token_url = "https://" + edl + "/api/users"


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
        logging.warning("There's no .netrc file or the The endpoint isn't in the netrc file")

    manager = request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, endpoint, username, password)
    auth = request.HTTPBasicAuthHandler(manager)

    jar = CookieJar()
    processor = request.HTTPCookieProcessor(jar)
    opener = request.build_opener(auth, processor)
    opener.addheaders = [('User-agent', 'podaac-subscriber-' + __version__)]
    request.install_opener(opener)



def get_token(url: str) -> str:
    tokens = list_tokens(url)
    if len(tokens) == 0 :
        return create_token(url)
    else:
        return tokens[0]

###############################################################################
# GET TOKEN FROM CMR
###############################################################################
@tenacity.retry(wait=tenacity.wait_random_exponential(multiplier=1, max=60),
                stop=tenacity.stop_after_attempt(3),
                reraise=True,
                retry=(tenacity.retry_if_result(lambda x: x == ''))
                )
def create_token(url: str) -> str:
    try:
        token: str = ''
        username, _, password = netrc.netrc().authenticators(edl)
        headers: Dict = {'Accept': 'application/json'}  # noqa E501


        resp = requests.post(url+"/token", headers=headers, auth=HTTPBasicAuth(username, password))
        response_content: Dict = json.loads(resp.content)
        if "error" in response_content:
            if response_content["error"] == "max_token_limit":
                logging.error("Max tokens acquired from URS. Using existing token")
                tokens=list_tokens(url)
                return tokens[0]
        token = response_content['access_token']

    # Add better error handling there
    # Max tokens
    # Wrong Username/Passsword
    # Other
    except:  # noqa E722
        logging.warning("Error getting the token - check user name and password", exc_info=True)
    return token


###############################################################################
# DELETE TOKEN FROM CMR
###############################################################################
def delete_token(url: str, token: str) -> bool:
    try:
        username, _, password = netrc.netrc().authenticators(edl)
        headers: Dict = {'Accept': 'application/json'}
        resp = requests.post(url+"/revoke_token",params={"token":token}, headers=headers, auth=HTTPBasicAuth(username, password))

        if resp.status_code == 200:
            logging.info("EDL token successfully deleted")
            return True
        else:
            logging.info("EDL token deleting failed.")

    except:  # noqa E722
        logging.warning("Error deleting the token", exc_info=True)

    return False

def list_tokens(url: str):
    try:
        tokens = []
        username, _, password = netrc.netrc().authenticators(edl)
        headers: Dict = {'Accept': 'application/json'}  # noqa E501
        resp = requests.get(url+"/tokens", headers=headers, auth=HTTPBasicAuth(username, password))
        response_content = json.loads(resp.content)

        for x in response_content:
            tokens.append(x['access_token'])

    except:  # noqa E722
        logging.warning("Error getting the token - check user name and password", exc_info=True)
    return tokens


def refresh_token(old_token: str):
    setup_earthdata_login_auth(edl)
    delete_token(token_url,old_token)
    return get_token(token_url)


def validate(args):
    if args.bbox is not None:
        bounds = args.bbox.split(',')
        if len(bounds) != 4:
            raise ValueError(
                "Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")  # noqa E501
        try:
            num_bounds = [float(b) for b in bounds]
        except ValueError:
            raise ValueError(
                "Error parsing '--bounds': " + args.bbox + ". Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces ")  # noqa E501

        if num_bounds[1] > num_bounds[3]:
            raise ValueError('Error parsing "--bounds": S Latitude must be <= N Latitude')


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

    if 'minutes' in args:
        if args.minutes:
            try:
                int(args.minutes)
            except ValueError:
                raise ValueError(
                    "Error parsing '--minutes': " + args.minutes + ". Number must be an integer.")  # noqa E501

    # Error catching for output directory specifications
    # Must specify -d output path or one time-based output directory flag
    if sum([args.cycle, args.dydoy, args.dymd, args.dy]) > 1:
        raise ValueError('Too many output directory flags specified, '
                         'Please specify exactly one flag '
                         'from -dc, -dy, -dydoy, or -dymd')

    if args.subset and args.search_cycles:
        # Cycle+Subset are not supported, because Harmony does not
        # currently accept Cycle.
        raise ValueError(
            'Error: Incompatible Parameters. You\'ve provided both cycles and subset, which is '
            'not allowed. Please provide either cycles or subset separately, but not both.')

    if args.subset and args.bbox:
        bounds = list(map(float, args.bbox.split(',')))
        if bounds[0] > bounds[2]:
            raise ValueError(
                'Subsetting over the international dateline is not currently supported. '
                'Please provide a valid bbox and try again.'
            )


def check_dir(path):
    if not isdir(path):
        makedirs(path, exist_ok=True)


def prepare_time_output(times, prefix, file, args, ts_shift):
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


def process_file(process_cmd, output_path, args):
    if not process_cmd:
        return
    else:
        for cmd in process_cmd:
            if args.verbose:
                logging.info(f'Running: {cmd} {output_path}')
            subprocess.run(cmd.split() + [output_path],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


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


def download_file(remote_file, output_path, retries=3):
    failed = False
    for r in range(retries):
        try:
            urlretrieve(remote_file, output_path)
        except HTTPError as e:
            if e.code == 503:
                logging.warning(f'Error downloading {remote_file}. Retrying download.')
                # back off on sleep time each error...
                time.sleep(r)
                # range is exclusive, so range(3): 0,1,2 so retries will
                # never be >= 3; need to subtract 1 (doh)
                if r >= retries-1:
                    failed = True
        else:
            #downlaoded fie without 503
            break

        if failed:
            raise Exception("Could not download file.")


# Retry using random exponential backoff if a 500 error is raised. Maximum 10 attempts.
@tenacity.retry(wait=tenacity.wait_random_exponential(multiplier=1, max=60),
                stop=tenacity.stop_after_attempt(10),
                reraise=True,
                retry=(tenacity.retry_if_exception_type(HTTPError) & tenacity.retry_if_exception(
                    lambda exc: exc.code == 500))
                )
def get_search_results(params, verbose=False):
    # Get the query parameters as a string and then the complete search url:
    query = urlencode(params)
    url = "https://" + cmr + "/search/granules.umm_json?" + query
    if verbose:
        logging.info(url)

    # Get a new timestamp that represents the UTC time of the search.
    # Then download the records in `umm_json` format for granules
    # that match our search parameters:
    results = None
    search_after_header = None
    while True:
        # Build the request, add the search after header to it if it's not None (e.g. after the first iteration)
        req = Request(url)
        if search_after_header is not None:
            req.add_header('CMR-Search-After', search_after_header)
        response = urlopen(req)

        # Build the results object, load entire result if it's the first time.
        if results is None:
            results = json.loads(response.read().decode())
        # if not the first time, add the new items to the existing array
        else:
            results['items'].extend(json.loads(response.read().decode())['items'])

        # get the new Search After header, if it's not set, we have all the results and we're done.
        search_after_header = None
        search_after_header = response.info()['CMR-Search-After']
        if search_after_header is not None:
            logging.debug("Search After response header defined, paging CMR for more data.")
        else:
            break
    # return all of the paged CMR results.
    return results


def parse_start_times(results):
    try:
        file_start_times = [(r['meta']['native-id'],
                             datetime.strptime((r['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']),
                                               "%Y-%m-%dT%H:%M:%S.%fZ")) for r in results['items']]  # noqa E501
    except KeyError:
        raise ValueError('Could not locate start time for data.')
    return file_start_times


def parse_cycles(results):
    try:
        cycles = [(splitext(r['meta']['native-id'])[0],
                   str(r['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Cycle'])) for r in
                  results['items']]  # noqa E501
    except KeyError:
        raise ValueError('No cycles found within collection granules. '
                         'Specify an output directory or '
                         'choose another output directory flag other than -dc.')  # noqa E501
    return cycles


def extract_checksums(granules):
    """
    Create a dictionary containing checksum information from files.

    Parameters
    ----------
    granule_results : dict
        The cmr granule search results (umm_json format)

    Returns
    -------
    A dictionary where the keys are filenames and the values are
    checksum information (checksum value and checksum algorithm).

    For Example:
    {
        "some-granule-name.nc": {
            "Value": "d96387295ea979fb8f7b9aa5f231c4ab",
            "Algorithm": "MD5"
        },
        "some-granule-name.nc.md5": {
            "Value": '320876f087da0876edc0876ab0876b7a",
            "Algorithm": "MD5"
        },
        ...
    }
    """
    checksums = {}
    for granule in granules:
        try:
            items = granule["umm"]["DataGranule"]["ArchiveAndDistributionInformation"]
            for item in items:
                try:
                    checksums[item["Name"]] = item["Checksum"]
                except:
                    pass
        except:
            pass
    return checksums


def checksum_does_match(file_path, checksums):
    """
    Checks if a file's checksum matches a checksum in the checksums dict

    Parameters
    ----------
    file_path : string
        The relative or absolute path to an existing file

    checksums: dict
        A dictionary where keys are filenames (not including the path)
        and values are checksum information (checksum value and checksum algorithm)

    Returns
    -------
    True - if the file's checksum matches a checksum in the checksum dict
    False - if the file doesn't have a checksum, or if the checksum doesn't match
    """
    filename = basename(file_path)
    checksum = checksums.get(filename)
    if not checksum:
        return False

    computed_checksum = make_checksum(file_path, checksum["Algorithm"])
    checksums_match = computed_checksum == checksum["Value"]
    if not checksums_match:
        logging.warning(f'Computed checksum {computed_checksum} does not match expected checksum {checksum["Value"]}')
    return checksums_match


def make_checksum(file_path, algorithm):
    """
    Create checksum of file using the specified algorithm
    """
    # Based on https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file#answer-3431838
    # with modification to handle multiple algorithms
    hashlib_algorithm_name = algorithm.lower().replace("-", "")
    hash_alg = hashlib.new(hashlib_algorithm_name)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_alg.update(chunk)
    return hash_alg.hexdigest()

def get_cmr_collections(params, verbose=False):
    query = urlencode(params)
    url = "https://" + cmr + "/search/collections.umm_json?" + query
    if verbose:
        logging.info(url)

    # Build the request, add the search after header to it if it's not None (e.g. after the first iteration)
    req = Request(url)
    response = urlopen(req)
    result = json.loads(response.read().decode())
    return result


def get_cmr_collection_id(collection_short_name, provider, token, verbose):
    """
    Retrieve collection ID from CMR given the collection short name and provider

    Parameters
    ----------
    collection_short_name: str
        The name of the collection
    provider: str
        The collection provider
    token: str
        The EDL token used to query CMR
    verbose: bool
        If true, print extra messages to stdout

    Returns
    -------
    str
        CMR collection concept ID

    Raises
    ------
    ValueError
        If no collection in CMR match the given short name and provider
    """
    params = {
        'provider': provider,
        'ShortName': collection_short_name,
        'token': token
    }
    collections = get_cmr_collections(params, verbose)['items']

    if not collections:
        raise ValueError(f'No collections found in CMR for {collection_short_name}/{provider}')
    return collections[0]['meta']['concept-id']


def create_citation(collection_json, access_date):
    citation_template = "{creator}. {year}. {title}. Ver. {version}. PO.DAAC, CA, USA. Dataset accessed {access_date} at {doi_authority}/{doi}"

    # Better error handling here may be needed...
    doi = collection_json['DOI']["DOI"]
    doi_authority = collection_json['DOI']["Authority"]
    citation = collection_json["CollectionCitations"][0]
    creator = citation["Creator"]
    release_date = citation["ReleaseDate"]
    title = citation["Title"]
    version = citation["Version"]
    year = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%S.000Z").year
    return citation_template.format(creator=creator, year=year, title=title, version=version, doi_authority=doi_authority, doi=doi, access_date=access_date)

def search_extension(extension, filename):
    if re.search(extension + "$", filename) is not None:
        return True
    return False

def create_citation_file(short_name, provider, data_path, token=None, verbose=False):
    # get collection umm-c METADATA
    params = [
        ('provider', provider),
        ('ShortName', short_name)
    ]
    if token is not None:
        params.append(('token', token))

    collection = get_cmr_collections(params, verbose)['items'][0]

    access_date = datetime.now().strftime("%Y-%m-%d")

    # create citation from umm-c metadata
    citation = create_citation(collection['umm'], access_date)
    # write file

    with open(data_path + "/" + short_name + ".citation.txt", "w") as text_file:
        text_file.write(citation)


def get_latest_release():
    github_url = "https://api.github.com/repos/podaac/data-subscriber/releases"
    headers = {}
    ghtoken = os.environ.get('GITHUB_TOKEN', None)
    if ghtoken is not None:
        headers = {"Authorization": "Bearer " + ghtoken}

    releases_json = requests.get(github_url, headers=headers).json()
    latest_release = get_latest_release_from_json(releases_json)
    return latest_release

def release_is_current(latest_release, this_version):
    return  not (version.parse(this_version) < version.parse(latest_release))

def get_latest_release_from_json(releases_json):
    releases = []
    for x in releases_json:
        releases.append(x['tag_name'])
    sorted(releases, key=lambda x: version.Version(x)).reverse()
    return releases[0]


def check_for_latest():
    try:
        latest_version = get_latest_release()
        if not release_is_current(latest_version,__version__):
            print(f'You are currently using version {__version__} of the PO.DAAC Data Subscriber/Downloader. Please run:\n\n pip install podaac-data-subscriber --upgrade \n\n to upgrade to the latest version.')
    except:
        print("Error checking for new version of the po.daac data subscriber. Continuing")


def is_collection_harmony_subsettable(concept_id, token=None):
    """
    Function to determine if a collection has an applicable harmony
    subsetter. This is accomplished by querying the CMR GraphQL API and
    looking for the expected UMM-S association.

    Parameters
    ----------
    concept_id: str
        The CMR collection concept ID to search for
    token: str
        EDL token used to query CMR

    Returns
    -------
    bool
        True if the collection is Harmony subsettable
    """
    graph_query_template = '''
    query Collection {
      collection(conceptId: "$TEMPLATE_CONCEPT_ID") {
        services{
          items {
            name
            serviceKeywords
            type
          }
        }
      }
    }
    '''
    query = graph_query_template.replace('$TEMPLATE_CONCEPT_ID', concept_id)
    headers = {}
    if token:
        headers = {'Authorization': 'Bearer ' + token}
    r = requests.post(graph_url, json={'query': query}, headers=headers, timeout=(10, 60))
    collection_services = r.json()['data']['collection']['services']['items']
    harmony_subsetter = False
    if collection_services is None:
        return False
    for svc in collection_services:
        if svc['type'] == 'Harmony':
            for kw in svc['serviceKeywords']:
                if kw['serviceTerm'] == 'SUBSETTING/SUPERSETTING':
                    harmony_subsetter = True

    return harmony_subsetter


def get_harmony_file(data_dir):
    """
    Get Harmony statefile absolute path

    Parameters
    ----------
    data_dir: str
        Path to data download location
    Returns
    -------
    str or None
        If there is a Harmony statefile in the provided location,
        return the path to the file. Otherwise, return None.
    """
    if isfile(data_dir + '/.harmony'):
        return data_dir + '/.harmony'
    return None


def find_harmony_runs(collection, bbox, starttime, endtime, output_dir, granules=None):
    """
    Look for run in Harmony statefile

    Parameters
    ----------
    collection: str
        CMR collection ID
    bbox: str
        bbox string
    starttime: str
        Harmony request start time
    endtime: str
        Harmony request end time
    output_dir: str
        Where to download files
    granules: list
        Optional. List of granules provided in Harmony request

    Returns
    --------
    str or None
        If an existing job is found, the job ID will be returned.
        Otherwise, return None.
    """
    harmony_file = get_harmony_file(output_dir)
    if harmony_file is None:
        return None
    try:
        with open(harmony_file, 'r') as f:
            harmony_json = json.load(f)
            for x in harmony_json:
                if x['collection_id'] == collection and x['starttime'] == starttime and x[
                     'endtime'] == endtime and x['bbox'] == bbox and x['granules'] == granules:
                    return x['jobid']
    except FileNotFoundError:
        logging.warning('No .harmony file in the data directory. (Is this the first run?)')
    return None


def remove_harmony_run(job_id, output_dir):
    """
    In the event we need to delete a Harmony run from the save file,
    this method can do that using a jobID. This might be used in the
    case of Harmony failures.

    Parameters
    ----------
    job_id: str
        Harmony job ID
    output_dir: str
        Location of downloaded Harmony statefile
    """
    harmony_file = get_harmony_file(output_dir)
    harmony_json = []
    if harmony_file:
        with open(harmony_file, 'r') as f:
            harmony_json = json.load(f)
    harmony_json = [x for x in harmony_json if x['jobid'] != job_id]

    with open(output_dir + '/.harmony', 'w') as outfile:
        json.dump(harmony_json, outfile)


def save_harmony_run(collection, bbox, starttime, endtime, job_id, output_dir, granule_ids=None):
    """
    Save Harmony run to Harmony statefile

    Parameters
    ----------
    collection: str
        CMR collection ID
    bbox: str
        Harmony request bbox
    starttime: str
        Harmony request start time
    endtime: str
        Harmony request end time
    job_id: str
        Harmony job ID
    output_dir: str
        Harmony statefile location
    granule_ids: list or None
        None or list of granule IDs used in Harmony request
    """
    harmony_file = get_harmony_file(output_dir)
    harmony_json = []
    if harmony_file:
        f = open(harmony_file, 'r')
        harmony_json = json.load(f)
        f.close()
    harmony_run = {
        'collection_id': collection,
        'starttime': starttime,
        'endtime': endtime,
        'bbox': bbox,
        'jobid': job_id,
        'granules': granule_ids
    }
    harmony_json.append(harmony_run)

    with open(output_dir + '/.harmony', 'w') as outfile:
        json.dump(harmony_json, outfile)


# Function to utilize Harmony for subsetting a collection
def subset(concept_id, bbox, start_time, stop_time, granules=None, verbose=False):
    """
    Submit Harmony subset request

    Parameters
    ----------
    concept_id: str
        CMR collection concept ID
    bbox: str
        Spatial bounds to use in Harmony subset request
    start_time: str
        Lower temporal bound to use in Harmony subset request
    stop_time: str
        Upper temporal bound to use in Harmony subset request
    granules: list or None
        Optional. List of granules to explicitly provide to Harmony.
        If no list is provided, spatiotemporal bounds will be used to
        find valid granules in collection.
    verbose: boolean
        Optional. Default False. If True, log Harmony job details.

    Returns
    -------
    str
        Harmony job ID (uuid)

    """
    harmony_client = harmony.Client()
    collection = harmony.Collection(id=concept_id)
    harmony_args = dict(
        collection=collection,
        skip_preview=True,
        granule_id=granules,
        ignore_errors=True,
        temporal={}
    )

    if bbox:
        bbox_list = [float(bound) for bound in bbox.split(',')]
        harmony_args['spatial'] = harmony.BBox(
            bbox_list[0], bbox_list[1], bbox_list[2], bbox_list[3]
        )
    if start_time:
        harmony_args['temporal']['start'] = isoparse(start_time)
    if stop_time:
        harmony_args['temporal']['stop'] = isoparse(stop_time)
    if verbose:
        logging.info(f'Submitting Harmony subsetting job with parameters {harmony_args}')

    harmony_request = harmony.Request(**harmony_args)
    harmony_request.is_valid()
    job_id = harmony_client.submit(harmony_request)
    return job_id


def download_callback(process_cmd, args, future):
    """
    Callback which is called upon each granule after successfully
    downloaded

    Parameters
    ----------
    process_cmd: str
        Command to run on each granule after successful download
    args: argparse.Namespace
        Script args
    future: asyncio.Future
        Future to extract result (download location) from when complete
    """
    process_file(process_cmd, future.result(), args)


def download_subsetted_files(job_id, output_dir, args, force_download=False, process_cmd=None):
    """
    Download Harmony results locally

    Parameters
    ----------
    job_id: str
    output_dir: str
    args: argparse.Namespace
    force_download: bool
    process_cmd: str

    Returns
    -------
    str
        Harmony job status. Will be one of:
        - failed
        - canceled
        - paused
        - complete_with_errors
        - successful
        - running_with_errors
    """
    harmony_client = harmony.Client()
    try:
        harmony_iterator = harmony_client.iterator(job_id, output_dir, force_download)
        futures = list(map(lambda x: x['path'], harmony_iterator))
        for future in futures:
            future.add_done_callback(
                functools.partial(download_callback, process_cmd, args)
            )
        (done_futures, _) = concurrent.futures.wait(futures)
    except Exception as e:
        logging.error(f'Error processing harmony subsetting request: {e}')
        logging.error(f'Removing job id [{job_id}] from harmony statefile {output_dir}/.harmony')
        remove_harmony_run(job_id, output_dir)
    return harmony_client.status(job_id)
    # If an error occurs, should we "retry" it? Should we remove this from the .harmony file?
