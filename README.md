
# Scripted Access to PODAAC data

 ----

![N|Solid](https://podaac.jpl.nasa.gov/sites/default/files/image/custom_thumbs/podaac_logo.png)

The example script is to download data given a PO.DAAC collection shortname.
  - These scripts can be set up as a cron that runs every hour or set up to download data per user needs
  - PO.DAAC is providing this script as “starter” script for download -- advanced features can be added and it would be great if you can contribute these code back to PO.DAAC.
  - The search and download relies on an API as defined at https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html

## Step 1:  Get Earthdata Login     
This step is needed only if you dont have an Earthdata login already.
https://urs.earthdata.nasa.gov/
> The Earthdata Login provides a single mechanism for user registration and profile  management for all EOSDIS system components (DAACs, Tools, Services). Your Earthdata login   also helps the EOSDIS program better understand the usage of EOSDIS services to improve  user experience through customization of tools and improvement of services. EOSDIS data are  openly available to all and free of charge except where governed by international  agreements.



## Step 2:  Run the Script

Usage:
```
usage: podaac_data_subscriber.py [-h] -c COLLECTION -d OUTPUTDIRECTORY [-m MINUTES] [-b BBOX] [-e [EXTENSIONS [EXTENSIONS ...]]] [-ds DATASINCE] [--version]
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

## Note 1: netrc file
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

**If the script cannot find the netrc file, you will be prompted to enter the username and passowrd and the script wont be able to generate the CMR token**

## Advanced Usage

### Setting a bounding rectangle for filtering results

If you're interested in a specific region, you can set the bounds parameter on your request to filter data that passes through a certain area. This is useful in particular for non-global datasets (such as swath datasets) with non-global coverage per file.

```
-b BBOX, --bounds BBOX
                      The bounding rectangle to filter result in. Format is W Longitude,S Latitude,E Longitude,N Latitude without spaces. Due to an issue with parsing arguments, to use this command, please use the -b="-180,-90,180,90" syntax when calling from
                      the command line. Default: "-180,-90,180,90\.

```
An example of the -b usage:

```
python podaac_data_subscriber.py -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -b="-180,-90,180,90"
```

### Setting extensions

Some collections have many files. To download a specific set of files, you can set the extensions on which downloads are filtered. By default, ".nc" and ".h5" files are downloaded by default.

```
-e [EXTENSIONS [EXTENSIONS ...]], --extensions [EXTENSIONS [EXTENSIONS ...]]
                      The extensions of products to download. Default is [.nc, .h5]
```

An example of the -e usage:
```
python podaac_data_subscriber.py -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -e .nc .h5
```


### Changing how often the script runs

```
-m MINUTES, --minutes MINUTES
                       How often, in minutes, should the script run (default: 60 minutes).

```
An example of the -m flag:
```
python podaac_data_subscriber.py -c VIIRS_N20-OSPO-L2P-v2.61 -d ./data -m 10
```


## Note 2: Downloading all or specific files for a collection
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
