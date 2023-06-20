# Data Downloader: Bulk or one-time Scripted Access to PODAAC data

The PO.DAAC Data downloader is a python-based tool for bulk and one-off (or non-often) downloading of data from the PO.DAAC archive. Use this script if you want to download data based on a space or time every once and a while.

For installation and dependency information, please see the [top-level README](README.md).

```
$> podaac-data-downloader -h
usage: PO.DAAC bulk-data downloader [-h] -c COLLECTION -d OUTPUTDIRECTORY [--cycle SEARCH_CYCLES] [-sd STARTDATE] [-ed ENDDATE] [-f] [-b BBOX] [-dc] [-dydoy] [-dymd] [-dy] [--offset OFFSET] [-e EXTENSIONS] [-gr GRANULENAME] [--process PROCESS_CMD] [--version] [--verbose] [-p PROVIDER] [--limit LIMIT] [--dry-run]

optional arguments:
  -h, --help            show this help message and exit
  -c COLLECTION, --collection-shortname COLLECTION
                        The collection shortname for which you want to retrieve data.
  -d OUTPUTDIRECTORY, --data-dir OUTPUTDIRECTORY
                        The directory where data products will be downloaded.
  --cycle SEARCH_CYCLES
                        Cycle number for determining downloads. can be repeated for multiple cycles
  -sd STARTDATE, --start-date STARTDATE
                        The ISO date time after which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z
  -ed ENDDATE, --end-date ENDDATE
                        The ISO date time before which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z
  -f, --force           Flag to force downloading files that are listed in CMR query, even if the file exists and checksum matches
  -b BBOX, --bounds BBOX
                        The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b="-180,-90,180,90" syntax when calling from the command line.
                        Default: "-180,-90,180,90".
  -dc                   Flag to use cycle number for directory where data products will be downloaded.
  -dydoy                Flag to use start time (Year/DOY) of downloaded data for directory where data products will be downloaded.
  -dymd                 Flag to use start time (Year/Month/Day) of downloaded data for directory where data products will be downloaded.
  -dy                   Flag to use start time (Year) of downloaded data for directory where data products will be downloaded.
  --offset OFFSET       Flag used to shift timestamp. Units are in hours, e.g. 10 or -10.
  -e EXTENSIONS, --extensions EXTENSIONS
                        Regexps of extensions of products to download. Default is [.nc, .h5, .zip, .tar.gz, .tiff]
  -gr GRANULENAME, --granule-name GRANULENAME
                        Flag to download specific granule from a collection. This parameter can only be used if you know the granule name. Only one granule name can be supplied. Supports wildcard search patterns allowing the user to identify multiple granules for download by using `?` for single- and `*` for multi-character expansion.
  --process PROCESS_CMD
                        Processing command to run on each downloaded file (e.g., compression). Can be specified multiple times.
  --version             Display script version information and exit.
  --verbose             Verbose mode.
  -p PROVIDER, --provider PROVIDER
                        Specify a provider for collection search. Default is POCLOUD.
  --limit LIMIT         Integer limit for number of granules to download. Useful in testing. Defaults to no limit.
  --dry-run             Search and identify files to download, but do not actually download them

```

## Step 2:  Run the Script

Usage:
```
usage: PO.DAAC bulk-data downloader [-h] -c COLLECTION -d OUTPUTDIRECTORY [--cycle SEARCH_CYCLES] [-sd STARTDATE] [-ed ENDDATE] [-f] [-b BBOX] [-dc] [-dydoy] [-dymd] [-dy] [--offset OFFSET] [-e EXTENSIONS] [-gr GRANULENAME] [--process PROCESS_CMD] [--version] [--verbose]
                                    [-p PROVIDER] [--limit LIMIT] [--dry-run]
```

To run the script, the following parameters are required:

```
-c COLLECTION, --collection-shortname COLLECTION
                        The collection shortname for which you want to retrieve data.
-d OUTPUTDIRECTORY, --data-dir OUTPUTDIRECTORY
                        The directory where data products will be downloaded.
```

And one of

```
-sd STARTDATE, --start-date STARTDATE
                      The ISO date time before which data should be retrieved. For Example, --start-date 2021-01-14T00:00:00Z
-ed ENDDATE, --end-date ENDDATE
                      The ISO date time after which data should be retrieved. For Example, --end-date 2021-01-14T00:00:00Z
--cycle SEARCH_CYCLES
                      Cycle number for determining downloads. can be repeated for multiple cycles                
```


`COLLECTION` is collection shortname of interest. This can be found from the PO.DAAC Portal, CMR, or earthdata search. Please see the included `Finding_shortname.pdf` document on how to find a collection shortname.

`OUTPUTDIRECTORY` is the directory in which files will be downloaded. It's customary to set this to a data directory and include the collection shortname as part of the path so if you run multiple subscribers, the data are not dumped into the same directory.

One last required item is a time entry, one of `--start-date`, `--end-date`, or `--cycle` must be specified. This is done so that a time is explicitly requested, and fewer assumptions are made about how the users is running the downloader.

The Script will login to CMR and the PO.DAAC Archive using a **netrc** file. See Note 1 for more information on setting this up.

Unlike the 'subscriber', no 'state' is maintained for the downloader. if you re-run the downloader you'll re-download all of the files again, unlike the subscriber which will download newly ingested data *since* the last run.

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

## Advanced Usage

### Download data by filename

If you're aware of a file you want to download, you can use the `-gr` option to download by a filename. The `-c` (COLLECTION) and `-d` (directory) options are still required.

The `-gr` option works by taking the file name, removing the suffix and searching for a CMR entry called the granuleUR. Some examples of this include:

| Collection | Filename      | CMR GranuleUR |
| --- | ----------- | ----------- |
| MUR25-JPL-L4-GLOB-v04.2  | 20221206090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc      | 20221206090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2       |
| JASON_CS_S6A_L2_ALT_HR_STD_OST_NRT_F | S6A_P4_2__HR_STD__NR_077_039_20221212T181728_20221212T182728_F07.nc   | S6A_P4_2__HR_STD__NR_077_039_20221212T181728_20221212T182728_F07        |

Because of this behavior, granules without data suffixes and granules where the the UR does not directly follow this convention may not work as anticipated. We will be adding the ability to download by granuleUR in a future enhancement.

The -gr option supports wildcard search patterns (using `?` for single- and `*` for multi-character expansion) to select and download multiple granules based on the filename pattern. This feature is supported through wildcard search functionality provided through CMR, which is described in the [CMR Search API documentation](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#parameter-options).

### Download data by cycle

Some PO.DAAC datasets are better suited for cycles based search instead of start and end times. To enabled this, we've added 'cycle' based downloading to the data-downloader. The following example will download data from cycle 42:

```
podaac-data-downloader -c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F -d ./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -dc  -b="-20,-20,20,20" --cycle 42
```
The cycle parameter can be repeated to specify multiple cycles:

```
podaac-data-downloader -c JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F -d ./JASON_CS_S6A_L2_ALT_LR_STD_OST_NRT_F  -dc  -b="-20,-20,20,20" --cycle 42 --cycle 43 --cycle 44
```


### Request data from another DAAC...

Use the 'provider' flag to point at a non-PO.DAAC provider. Be aware, the default data types (--extensions) may need to be specified if the desired data are not in the defaults.

```
podaac-data-downloader -c SENTINEL-1A_SLC -d myData  -p ASF -sd 2014-06-01T00:46:02Z -ed 2014-07-01T00:46:02Z
```

### Logging

For error troubleshooting, one can set an environment variable to gain more insight into errors:

```
export PODAAC_LOGLEVEL=DEBUG
```

And then run the script. This should give you more verbose output on URL requests to CMR, tokens, etc.

### Controlling output directories

The subscriber allows the placement of downloaded files into one of several directory structures based on the flags used to run the subscriber.

* -d - required, specifies the directory to which data is downloaded. If this is the only flag specified, all files will be downloaded to this single directory.
* -dc - optional, if 'cycle' information exists in the product metadata, download it to the data directory and use a relative c<CYCLE> path to store granules. The relative path is 0 padded to 4 total digits (e.g. c0001)
* -dydoy - optional, relative paths use the start time of a granule to layout data in a YEAR/DAY-OF-YEAR path
* -dymd  - optional, relative paths use the start time of a granule to layout data in a YEAR/MONTH/DAY path


### Downloader behavior when a file already exists

By default, when the downloader is about to download a file, it first:
- Checks if the file already exists in the target location
- Creates a checksum for the file and sees if it matches the checksum for that file in CMR

If the file already exists AND the checksum matches, the downloader will skip downloading that file.

This can drastically reduce the time for the downloader to complete. Also, since the checksum is verified, files will still be re-downloaded if for some reason the file has changed (or the file already on disk is corrupted).

You can override this default behavior - forcing the downloader to always download matching files, by using --force/-f.

```
podaac-data-downloader -c SENTINEL-1A_SLC -d myData -f
```

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
podaac-data-downloader -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -b="-180,-90,180,90" -sd 2020-06-01T00:46:02Z -ed 2020-07-01T00:46:02Z
```

### Setting extensions

Some collections have many files. To download a specific set of files, you can set the extensions on which downloads are filtered. By default, ".nc", ".h5", and ".zip" files are downloaded by default. The `-e` option is a regular expression check so you can do advanced things like `-e PTM_\\d+` to match `PTM_` followed by one or more digits- useful when the ending of a file has no suffix and has a number (1-12 for PTM, in this example)

```
-e EXTENSIONS, --extensions EXTENSIONS
                      Regexps of extensions of products to download. Default is [.nc, .h5, .zip, .tar.gz, .tiff]
```

An example of the -e usage- note the -e option is additive:
```
podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -e .nc -e .h5 -sd 2020-06-01T00:46:02Z -ed 2020-07-01T00:46:02Z
```

One may also specify a regular expression to select files. For example, the following are equivalent:

`podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -e PTM_1, -e PTM_2, ...,  -e PMT_10 -sd 2020-06-01T00:46:02Z -ed 2020-07-01T00:46:02Z`

and

`podaac-data-subscriber -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -e PTM_\\d+ -sd 2020-06-01T00:46:02Z -ed 2020-07-01T00:46:02Z`


### run a post download process

Using the `--process` option, you can run a simple command agaisnt the "just" downloaded file. This will take the format of "<command> <path/to/file>". This means you can run a command like `--process gzip` to gzip all downloaded files. We do not support more advanced processes at this time (piping, running a process on a directory, etc).



### In need of Help?
The PO.DAAC User Services Office is the primary point of contact for answering your questions concerning data and information held by the PO.DAAC. User Services staff members are knowledgeable about both the data ordering system and the data products themselves. We answer questions about data, route requests to other DAACs, and direct questions we cannot answer to the appropriate information source.

Please contact us via email at podaac@podaac.jpl.nasa.gov
