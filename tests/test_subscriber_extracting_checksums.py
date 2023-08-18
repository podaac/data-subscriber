import json
from subscriber.podaac_access import extract_checksums

minimal_granule_search_results = """{
  "hits": 13,
  "took": 51,
  "items": [
    {
      "umm": {
        "DataGranule": {
          "ArchiveAndDistributionInformation": [
            {
              "SizeUnit": "MB",
              "Size": 4.312029838562012,
              "Checksum": {
                "Value": "d96387295ea979fb8f7b9aa5f231c4ab",
                "Algorithm": "MD5"
              },
              "SizeInBytes": 4521491,
              "Name": "20211231000000-REMSS-L3U_GHRSST-SSTsubskin-AMSR2-f34_20211231v8-v02.0-fv01.0.nc"
            },
            {
              "SizeUnit": "MB",
              "Size": 1.068115234375e-4,
              "Checksum": {
                "Value": "8704789dd2cad4554481f6e438acb376",
                "Algorithm": "MD5"
              },
              "SizeInBytes": 112,
              "Name": "20211231000000-REMSS-L3U_GHRSST-SSTsubskin-AMSR2-f34_20211231v8-v02.0-fv01.0.nc.md5"
            }
          ]
        }
      }
    },
    {
      "umm": {
        "DataGranule": {
          "ArchiveAndDistributionInformation": [
            {
              "SizeUnit": "MB",
              "Size": 4.267633438110352,
              "SizeInBytes": 4474938,
              "Name": "this-shouldnt-be-counted-because-theres-no-checksum-info.nc"
            }
          ]
        }
      }
    },
    {
      "umm": {
        "DataGranule": {
          "ArchiveAndDistributionInformation": [
            {
              "SizeUnit": "MB",
              "Size": 4.267633438110352,
              "SizeInBytes": 4474938,
              "Name": "this-also-shouldnt-be-counted-because-no-checksum-info.nc"
            },
            {
              "SizeUnit": "MB",
              "Size": 4.267633438110352,
              "Checksum": {
                "Value": "98d330cad6d1233c258178bcc07102d6",
                "Algorithm": "MD5"
              },
              "SizeInBytes": 4474938,
              "Name": "this-should-be-counted.nc"
            }
          ]
        }
      }
    },
    {
      "umm": {
        "DataGranule": {
          "ArchiveAndDistributionInformation": [
            {
              "SizeUnit": "MB",
              "Size": 4.267633438110352,
              "Checksum": {
                "Value": "98d330cad6d1233c258178bcc07102d6",
                "Algorithm": "MD5"
              },
              "SizeInBytes": 4474938,
              "Name": "20220101000000-REMSS-L3U_GHRSST-SSTsubskin-AMSR2-f34_20220101v8-v02.0-fv01.0.nc"
            },
            {
              "SizeUnit": "MB",
              "Size": 1.068115234375e-4,
              "Checksum": {
                "Value": "667a931589ec574acbf8791b73aeff1a",
                "Algorithm": "MD5"
              },
              "SizeInBytes": 112,
              "Name": "20220101000000-REMSS-L3U_GHRSST-SSTsubskin-AMSR2-f34_20220101v8-v02.0-fv01.0.nc.md5"
            }
          ]
        }
      }
    }
  ]
}
"""

def test_extract_checksums():
  checksums = extract_checksums(json.loads(minimal_granule_search_results)['items'])
  assert checksums["20211231000000-REMSS-L3U_GHRSST-SSTsubskin-AMSR2-f34_20211231v8-v02.0-fv01.0.nc"] == {
                "Value": "d96387295ea979fb8f7b9aa5f231c4ab",
                "Algorithm": "MD5"
              }
  assert len(checksums) == 5

