# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [1.15.2]
### Fixed
- Fixed bug where --subset in combination with the subscriber caused errors
### Added

## [1.15.0]
### Added
- Added support for Harmony subsetting

## [1.14.0]
### Added
- Added support for wildcard search patterns in podaac-data-downloader when executed with the -gr option (i.e. search/download by CMR Granule Ur/Id). Also, added usage details to Downloader.md to describe this new feature [138](https://github.com/podaac/data-subscriber/pull/138).

## 1.13.1
### Fixed
- Fixed an issue where a required library wasn't being included in the installation.

## 1.13.0
### Added
- Added --dry-run option to subscriber and downloader to view the files that _would_ be downloaded without actuall downloading them. [102](https://github.com/podaac/data-subscriber/issues/102)
- Added new feature allowing regex to be used in `--extension` `-e` options. For example using -e `PTM_\\d+` would match data files like `filename.PTM_1`, `filename.PTM_2` and `filename.PTM_10`, instead of specifying all possible combinations (`-e PTM_1, -e PTM_2, ...,  -e PMT_10`) [115](https://github.com/podaac/data-subscriber/issues/115)
- Added check for updated version [70](https://github.com/podaac/data-subscriber/issues/70)
- Removed CMR Token from log messages [127](https://github.com/podaac/data-subscriber/issues/127)


## 1.12.0
### Fixed
- Added EDL based token downloading, removing CMR tokens [98](https://github.com/podaac/data-subscriber/issues/98),
### Added
- Added ability to download by filename [109](https://github.com/podaac/data-subscriber/issues/109) and additional regression testing

## 1.11.0
### Fixed
- Fixed an issue where token-refresh was expecting a dictionary, not a list of tuples
- Fixed issues where token was not propagated to downloader CMR query [94](https://github.com/podaac/data-subscriber/issues/94)
- Fixed an issue with 503 errors on data download not being re-tried. [97](https://github.com/podaac/data-subscriber/issues/9797)
- added ".tiff" to default extensions to address #[100](https://github.com/podaac/data-subscriber/issues/100)
- removed erroneous 'warning' message on not downloading all data to close [99](https://github.com/podaac/data-subscriber/issues/99)
- updated help documentation for start/end times to close [79](https://github.com/podaac/data-subscriber/issues/79)
### Added
- Added citation file creation when data are downloaded [91](https://github.com/podaac/data-subscriber/issues/91). Required some updates to the regression testing.

## [1.10.2]
### Fixed
- Fixed an issue where using a default global bounding box prevented download of data that didn't use the horizontal spatial domain [87](https://github.com/podaac/data-subscriber/issues/87)
- Fixed limit option not being respected. [86](https://github.com/podaac/data-subscriber/issues/86)

## [1.10.1]
### Fixed
- Support for SHA-256 and SHA-512 checksums

## [1.10.0]
### Changed
- Changed minimum supported python version to 3.7, down from 3.8.

## [1.9.1]
### Changed
- Switched to [poetry](https://python-poetry.org/) as the build tool for the project

## [1.9.0]
### Added
- check if file exists before downloading a file. [17](https://github.com/podaac/data-subscriber/issues/17)
- added automated regression testing
### Changed
- Implemented Search After CMR interface to allow granule listings > 2000 [15](https://github.com/podaac/data-subscriber/issues/15)
- Retry CMR queries on server error using random exponential backoff max 60 seconds and 10 retries
- Refresh token if CMR returns 401 error
- Converted print statements to log statements
### Deprecated
### Removed
### Fixed
### Security

## [1.8.0]
### Added
- limit to set limit of downloads- useful for testing
- cycle based downloads to the podaac-data-downloader. [41](https://github.com/podaac/data-subscriber/issues/41)
- conftest.py added to force module inclusion for pytest
- podaac-data-downloader script for bulk data downloading
### Changed
- created library of common access mechanisms to split between subscriber and downloader capabilities
- added .tar.gz to list of default extensions. [40](https://github.com/podaac/data-subscriber/issues/40)
- Ignore error if destination directory already exists. [46](https://github.com/podaac/data-subscriber/issues/46)
- Updated the naming convention of .update file. [44](https://github.com/podaac/data-subscriber/issues/44)
- one of -m, -sd, or -ed must be given to subscriber. Previously -m 60 was the default if nothing was specified.
### Deprecated
- use of ".update" file naming convention. This will still work, but will be renamed to .update__COLLECTIONNAME after a successful run. the ".update" file will need to be manually cleaned up. See [issue 44](https://github.com/podaac/data-subscriber/issues/44)
### Removed
### Fixed
- issue where only specifying an end data cause issues in subscriber. [39](https://github.com/podaac/data-subscriber/issues/39)
### Security

## [1.7.2]
### Added
### Changed
- Made number of files to download a non-verbose default printout. [33](https://github.com/podaac/data-subscriber/issues/33)
### Deprecated
### Removed
### Fixed
### Security

## [1.7.1]
### Added
- Auto build and deploy to pypi on tag/release.
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.7.0]
### Added
- Added ability to call a process on downlaoded files. [Thank to Joe Sapp](https://github.com/sappjw).
### Changed
- Turned -e option into 'additive' mode (multiple -e options allowed.) [Thanks to Joe Sapp](https://github.com/sappjw)
### Deprecated
### Removed
### Fixed
- issue not being able to find granuleUR [#28](https://github.com/podaac/data-subscriber/issues/28)
### Security

## [1.6.1]
### Added
- added warning for more than 2k granules
### Changed
### Deprecated
### Removed
### Fixed
- strip newline characters from .update to fix https://github.com/podaac/data-subscriber/issues/25
### Security

## [1.6.0]
### Added
- added --offset flag for timestamp shift when creating DOY folder - (resolves https://github.com/podaac/data-subscriber/issues/23)
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.5.0] - 2021-10-12
### Added
- added ability to change the provider using the -p/--provider flag. Default is 'POCLOUD'
- added pyproject info and setup.py fixes to enable pypi pushes
### Changed
- added pytest and flake8 fixes for automated builds
### Deprecated
### Removed
### Fixed
### Security

## [1.4.0] - 2021-10-05
### Added
### Changed
- changed changing created_at to updated_since to allow for re-download of updated granules based on collection redeliveries - (resolves https://github.com/podaac/data-subscriber/issues/18)
### Deprecated
### Removed
### Fixed
### Security


## [1.3.0] - 2021-08-26
### Added
- added additional non-flat output directory option of -dy - (resolves https://github.com/podaac/data-subscriber/issues/13)
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.2.0] - 2021-08-15
### Added
- Added logging capability using the SUBSCRIBER_LOGLEVEL environment variable
- Added -st and -ed flags and respect the .update flag
### Changed
### Deprecated
### Removed
- removed the -ds flag as it caused confusion.
### Fixed
### Security

## [1.1.2] - 2021-06-20
### Added
- added default layouts for non-flat output directories - (resolves https://github.com/podaac/data-subscriber/issues/6)
- Added logging capability using the SUBSCRIBER_LOGLEVEL environment variable
- added additional non-flat output directory option of -dy - (resolves https://github.com/podaac/data-subscriber/issues/13)
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.1.1] - 2021-06-06
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
- updated urllib3>=1.26.5 (fixes https://github.com/advisories/GHSA-q2q7-5pp4-w6pg)

## [1.1.0] - 2021-05-28
### Added
- User Agent to request so we can determine better support posture based on metrics
### Changed
### Deprecated
### Removed
### Fixed
### Security


## [1.0.0] - 2021-05-13
### Added
- data subscriber functionality
### Changed
### Deprecated
### Removed
### Fixed
### Security
