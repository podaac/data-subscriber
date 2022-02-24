[![Python Build](https://github.com/podaac/data-subscriber/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/podaac/data-subscriber/actions/workflows/python-app.yml)
[![PyPi release](https://github.com/podaac/data-subscriber/actions/workflows/release.yml/badge.svg)](https://github.com/podaac/data-subscriber/actions/workflows/release.yml)


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

The subscriber and downloader scripes are available in the [pypi python repository](https://pypi.org/project/podaac-data-subscriber/), it can be installed via pip:

```
pip install podaac-data-subscriber
```

you should now have access to the downloader and subscriber Command line interfaces:

```
$> podaac-data-subscriber -h
usage: podaac_data_subscriber.py [-h] -c COLLECTION -d OUTPUTDIRECTORY [-sd STARTDATE] [-ed ENDDATE] [-b BBOX] [-dc] [-dydoy] [-dymd] [-dy] [--offset OFFSET] [-m MINUTES]
                                 [-e EXTENSIONS] [--process PROCESS_CMD] [--version] [--verbose] [-p PROVIDER]

...
```

## Step 1:  Get Earthdata Login     
This step is needed only if you dont have an Earthdata login already.
https://urs.earthdata.nasa.gov/
> The Earthdata Login provides a single mechanism for user registration and profile  management for all EOSDIS system components (DAACs, Tools, Services). Your Earthdata login   also helps the EOSDIS program better understand the usage of EOSDIS services to improve  user experience through customization of tools and improvement of services. EOSDIS data are  openly available to all and free of charge except where governed by international  agreements.

For setting up your authentication, see the notes on the `netrc` file below.

## Step 2: Setup your Earthdata Login
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


### In need of Help?
The PO.DAAC User Services Office is the primary point of contact for answering your questions concerning data and information held by the PO.DAAC. User Services staff members are knowledgeable about both the data ordering system and the data products themselves. We answer questions about data, route requests to other DAACs, and direct questions we cannot answer to the appropriate information source.

Please contact us via email at podaac@podaac.jpl.nasa.gov
