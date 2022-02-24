from urllib import request
from http.cookiejar import CookieJar
import netrc
import requests
import json
from os import makedirs
from os.path import isdir, basename, join, splitext
import subprocess
from urllib.parse import urlencode
from urllib.request import urlopen
from datetime import datetime

__version__ = "1.8.0"
extensions = [".nc", ".h5", ".zip", ".tar.gz"]
edl = "urs.earthdata.nasa.gov"
cmr = "cmr.earthdata.nasa.gov"
token_url = "https://" + cmr + "/legacy-services/rest/tokens"

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
def get_token(url: str, client_id: str, endpoint: str) -> str:
    try:
        token: str = ''
        username, _, password = netrc.netrc().authenticators(endpoint)
        xml: str = """<?xml version='1.0' encoding='utf-8'?>
        <token><username>{}</username><password>{}</password><client_id>{}</client_id>
        <user_ip_address>{}</user_ip_address></token>""".format(username, password, client_id, IPAddr)   # noqa E501
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

    if 'minutes' in args:
        if args.minutes:
            try:
                int(args.minutes)
            except ValueError:
                raise ValueError("Error parsing '--minutes': " + args.minutes + ". Number must be an integer.")  # noqa E501

    # Error catching for output directory specifications
    # Must specify -d output path or one time-based output directory flag
    if sum([args.cycle, args.dydoy, args.dymd, args.dy]) > 1:
        raise ValueError('Too many output directory flags specified, '
                         'Please specify exactly one flag '
                         'from -dc, -dy, -dydoy, or -dymd')


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
                print(f'Running: {cmd} {output_path}')
            subprocess.run(cmd.split() + [output_path],
                           check=True)


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


def get_search_results(args, params):
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
    return results


def parse_start_times(results):
    try:
        file_start_times = [(r['meta']['native-id'], datetime.strptime((r['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']), "%Y-%m-%dT%H:%M:%S.%fZ")) for r in results['items']]  # noqa E501
    except KeyError:
        raise ValueError('Could not locate start time for data.')
    return file_start_times


def parse_cycles(results):
    try:
        cycles = [(splitext(r['meta']['native-id'])[0],str(r['umm']['SpatialExtent']['HorizontalSpatialDomain']['Track']['Cycle'])) for r in results['items']]  # noqa E501
    except KeyError:
        raise ValueError('No cycles found within collection granules. '
                         'Specify an output directory or '
                         'choose another output directory flag other than -dc.')  # noqa E501
    return cycles
