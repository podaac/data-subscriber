# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)


## Unreleased
### Added
### Changed
- Made number of files to download a non-verbose default printout. [33](https://github.com/podaac/data-subscriber/issues/33)
### Deprecated
### Removed
### Fixed
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
