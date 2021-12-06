[![Python Build](https://github.com/podaac/data-subscriber/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/podaac/data-subscriber/actions/workflows/python-app.yml)

# Scripted Access to PODAAC data

 ----

![N|Solid](https://podaac.jpl.nasa.gov/sites/default/files/image/custom_thumbs/podaac_logo.png)

The example script is to download data given a PO.DAAC collection shortname.
  - These scripts can be set up as a cron that runs every hour or set up to download data per user needs
  - PO.DAAC is providing this script as “starter” script for download -- advanced features can be added and it would be great if you can contribute these code back to PO.DAAC.
  - The search and download relies on an API as defined at https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html

If this is your first time running the subscriber, please checkout information on ["your first run"!](#your-first-run)

## Dependencies

Aside from **python 3**, the only dependency is the python 'requests' module, which can be installed via pip.

```
python -m pip install requests
```

## Installation

While the scubscriber is not available in the python repository, it can still be installed via pip:

```
python -m pip install git+https://github.com/podaac/data-subscriber.git
```

you should now have access to the subscriber CLI:

```
$> podaac-data-subscriber -h
usage: podaac_data_subscriber.py [-h] -c COLLECTION -d OUTPUTDIRECTORY [-sd STARTDATE] [-ed ENDDATE] [-b BBOX] [-dc] [-dydoy] [-dymd] [-dy] [--offset OFFSET] [-m MINUTES]
                                 [-e EXTENSIONS] [--process PROCESS_CMD] [--version] [--verbose] [-p PROVIDER]

optional arguments:
  -h, --help            show this help message and exit
  -c COLLECTION, --collection-shortname COLLECTION
                        The collection shortname for which you want to retrieve data.
  -d OUTPUTDIRECTORY, --data-dir OUTPUTDIRECTORY
                        The directory where data products will be downloaded.
  -sd STARTDATE, --start-date STARTDATE
                        The ISO date time before which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z
  -ed ENDDATE, --end-date ENDDATE
                        The ISO date time after which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z
  -b BBOX, --bounds BBOX
                        The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing
                        arguments, to use this command, please use the -b="-180,-90,180,90" syntax when calling from the command line. Default: "-180,-90,180,90".
  -dc                   Flag to use cycle number for directory where data products will be downloaded.
  -dydoy                Flag to use start time (Year/DOY) of downloaded data for directory where data products will be downloaded.
  -dymd                 Flag to use start time (Year/Month/Day) of downloaded data for directory where data products will be downloaded.
  -dy                   Flag to use start time (Year) of downloaded data for directory where data products will be downloaded.
  --offset OFFSET       Flag used to shift timestamp. Units are in hours, e.g. 10 or -10.
  -m MINUTES, --minutes MINUTES
                        How far back in time, in minutes, should the script look for data. If running this script as a cron, this value should be equal to or greater than how
                        often your cron runs (default: 60 minutes).
  -e EXTENSIONS, --extensions EXTENSIONS
                        The extensions of products to download. Default is [.nc, .h5, .zip]
  --process PROCESS_CMD
                        Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.
  --version             Display script version information and exit.
  --verbose             Verbose mode.
  -p PROVIDER, --provider PROVIDER
                        Specify a provider for collection search. Default is POCLOUD.
```

One can also call the python package directly:

```
git clone https://github.com/podaac/data-subscriber.git

Cloning into 'data-subscriber'...
remote: Enumerating objects: 35, done.
remote: Counting objects: 100% (35/35), done.
remote: Compressing objects: 100% (25/25), done.
remote: Total 35 (delta 14), reused 28 (delta 7), pack-reused 0
Receiving objects: 100% (35/35), 1.19 MiB | 704.00 KiB/s, done.
Resolving deltas: 100% (14/14), done.
$ cd data-subscriber/
$ python subscriber/podaac_data_subscriber.py -h
....
```

## Step 1:  Get Earthdata Login     
This step is needed only if you dont have an Earthdata login already.
https://urs.earthdata.nasa.gov/
> The Earthdata Login provides a single mechanism for user registration and profile  management for all EOSDIS system components (DAACs, Tools, Services). Your Earthdata login   also helps the EOSDIS program better understand the usage of EOSDIS services to improve  user experience through customization of tools and improvement of services. EOSDIS data are  openly available to all and free of charge except where governed by international  agreements.

For setting up your authentication, see the notes on the `netrc` file below.



## Step 2:  Run the Script

Usage:
```
usage: podaac_data_subscriber.py [-h] -c COLLECTION -d OUTPUTDIRECTORY [-sd STARTDATE] [-ed ENDDATE] [-b BBOX] [-dc] [-dydoy] [-dymd] [-dy] [--offset OFFSET]
                                 [-m MINUTES] [-e EXTENSIONS] [--version] [--verbose] [-p PROVIDER]
```

To run the script, the following parameters are required:

```
-c COLLECTION, --collection-shortname COLLECTION
                        The collection shortname for which you want to retrieve data.
-d OUTPUTDIRECTORY, --data-dir OUTPUTDIRECTORY
                        The directory where data products will be downloaded.
```

`COLLECTION` is collection shortname of interest. This can be found from the PO.DAAC Portal, CMR, or earthdata search. Please see the included `Finding_shortname.pdf` document on how to find a collection shortname.

`OUTPUTDIRECTORY` is the directory in which files will be downloaded. It's customary to set this to a data directory and include the collection shortname as part of the path so if you run multiple subscribers, the data are not dumped into the same directory.

The Script will login to CMR and the PO.DAAC Archive using a netrc file. See Note 1 for more information on setting this up.

Every time the script runs successfully (that is, no errors), a `.update` file is created in your download directory with the last run timestamp. This timestamp will be used the next time the script is run. It will look for data between the timestamp in that file and the current time to determine new files to download.

## Note: CMR times
There are numerous 'times' available to query on in CMR. For the default subscriber, we look at the 'created at' field, which will look for when a granule file was ingested into the archive. This means as PO.DAAC gets data, your subscriber will also get data, regardelss of the time range within the granule itself.

## Note: netrc file
The netrc used within the script  will allow Python scripts to log into any Earthdata Login without being prompted for
credentials every time you run. The netrc file should be placed in your HOME directory.
To find the location of your HOME directory

On UNIX you can use
```
echo $HOME
```
On Windows you can use
```
echo %HOMEDRIVE%%HOMEPATH%
```

The output location from the command above should be the location of the `.netrc` (`_netrc` on Windows) file.

The format of the `netrc` file is as follows:

```
machine urs.earthdata.nasa.gov
    login <your username>
    password <your password>
```
for example:

```
machine urs.earthdata.nasa.gov
    login podaacUser
    password podaacIsAwesome
```

**If the script cannot find the netrc file, you will be prompted to enter the username and password and the script wont be able to generate the CMR token**

## Your First Run<a name="yfr"></a>

The first time you run the subscriber, there a few things to be aware of:

1. If no other flags are specified (aside from the required -d and -c), the subscriber looks 60 minutes (the default for the -m option) ago for new data for your data product. If no new data has been ingested in the last 60 minutes, you won't get any results. The next time you run this command, however, it will look for data *since the last run*, so if it's been an hour or 10 days since the last run, it will find any data since that time. This 'last run' time is stored in a file in the -d data download directory. If you change data directories, there will be no 'last run' time, and it will act like your first time.

Take for example a collection that was last updated in February of 2021.

```
podaac-data-subscriber -c CYGNSS_L1_CDR_V1.0 -d myData
NOTE: Making new data directory at myData(This is the first run.)
Downloaded: 0 files

Files Failed to download:0

CMR token successfully deleted
```

No data! What gives?! oh... because i'm not using any flags, I'm only looking back 60 minutes.

```
podaac-data-subscriber -c CYGNSS_L1_CDR_V1.0 -d myData --start-date 2021-02-25T00:00:00Z
2021-07-29 14:33:11.249343 SUCCESS: https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-protected/CYGNSS_L1_CDR_V1.0/cyg03.ddmi.s20210228-000000-e20210228-235959.l1.power-brcs-cdr.a10.d10.nc
...
```

Now we're getting data, great!

## Advanced Usage

### Request data from another DAAC...

Use the 'provider' flag to point at a non-PO.DAAC provider. Be aware, the default data types (--extensions) may need to be specified if the desired data are not in the defaults.

```
podaac-data-subscriber -c SENTINEL-1A_SLC -d myData  -p ASF -sd 2014-06-01T00:46:02Z
```

### Logging

For error troubleshooting, one can set an environment variable to gain more insight into errors:

```
export SUBSCRIBER_LOGLEVEL=DEBUG
```

And then run the script. This should give you more verbose output on URL requests to CMR, tokens, etc.

### Controlling output directories

The subscriber allows the placement of downloaded files into one of several directory structures based on the flags used to run the subscriber.

* -d - required, specifies the directory to which data is downloaded. If this is the only flag specified, all files will be downloaded to this single directory.
* -dc - optional, if 'cycle' information exists in the product metadata, download it to the data directory and use a relative c<CYCLE> path to store granules. The relative path is 0 padded to 4 total digits (e.g. c0001)
* -dydoy - optional, relative paths use the start time of a granule to layout data in a YEAR/DAY-OF-YEAR path
* -dymd  - optional, relative paths use the start time of a granule to layout data in a YEAR/MONTH/DAY path

### Running as a Cron job

To automatically run and update a local file system with data files from a collection, one can use a syntax like the following:

```
10 * * * * podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d /path/to/data/VIIRS_N20-OSPO-L2P-v2.61 -e .nc -e .h5 -m 60 -b="-180,-90,180,90" --verbose >> ~/.subscriber.log

```

This will run every hour at ten minutes passed, and output will be appended to a local file called ~/.subscriber.log

### Setting a bounding rectangle for filtering results

If you're interested in a specific region, you can set the bounds parameter on your request to filter data that passes through a certain area. This is useful in particular for non-global datasets (such as swath datasets) with non-global coverage per file.

***Note: This does not subset the data, it just uses file metadata to see if any part of the datafile passes through your region. This will download the entire file, including data outside of the region specified.***

```
-b BBOX, --bounds BBOX
                      The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b="-180,-90,180,90" syntax when calling from
                      the command line. Default: "-180,-90,180,90\.

```
An example of the -b usage:

```
podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -b="-180,-90,180,90"
```

### Setting extensions

Some collections have many files. To download a specific set of files, you can set the extensions on which downloads are filtered. By default, ".nc", ".h5", and ".zip" files are downloaded by default.

```
-e EXTENSIONS, --extensions EXTENSIONS
                       The extensions of products to download. Default is [.nc, .h5, .zip]
```

An example of the -e usage- note the -e option is additive:
```
podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -e .nc -e .h5
```
### run a post download process

Using the `--process` option, you can run a simple command agaisnt the "just" downloaded file. This will take the format of "<command> <path/to/file>". This means you can run a command like `--process gzip` to gzip all downloaded files. We do not support more advanced processes at this time (piping, running a process on a directory, etc).


### Changing how far back the script looks for data

Each time the script runs, the script takes the current time and looks -m minutes ago to determine what files it needs to download. the Default is 60 minutes. So it looks at files ingested within the last hour. This works well fi you run a cron job every 60 minutes.

**If the .update file exists in the output directory, that timestamp will override the -m flag.**

```
-m MINUTES, --minutes MINUTES
                       How far back in time, in minutes, should the script look for data. If running this script as a cron, this value should be equal to or greater than how often your cron runs (default: 60 minutes).

```
An example of the -m flag:
```
podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -m 10
```


## Note: Downloading all or specific files for a collection
The code is meant to be generic – for some data products, there is more than one file that can be a data files.
To get just the raw data file as defined by the metadata swap out
```
downloads_metadata = [[u['URL'] for u in r['umm']['RelatedUrls'] if u['Type']=="EXTENDED METADATA"] for r in results['items']]
```
to
```
downloads_metadata = []
```

```
downloads = [item for sublist in downloads_all for item in sublist]
filter_files = ['.nc', '.dat','.bin']  # This will only download netcdf, data, and binary files, you can add/remove other data types as you see fit
import re
def Filter(list1, list2):
    return [n for n in list1 if
             any(m in n for m in list2)]
downloads=Filter(downloads,filter_files)
```


### In need of Help?
The PO.DAAC User Services Office is the primary point of contact for answering your questions concerning data and information held by the PO.DAAC. User Services staff members are knowledgeable about both the data ordering system and the data products themselves. We answer questions about data, route requests to other DAACs, and direct questions we cannot answer to the appropriate information source.

Please contact us via email at podaac@podaac.jpl.nasa.gov
