from subscriber.podaac_data_subscriber import checksum_does_match

def test_checksum_does_match__positive_match_md5(tmpdir):
  output_path = str(tmpdir) + '/tmp.nc'
  checksums = {
    "tmp.nc": {
      "Value": "f83f9ad1718d9b95220ddd6b18dbcecf",
      "Algorithm": "MD5"
    }
  }

  with open(output_path, 'w') as f:
    f.write("This is a temporary test file\n")

  assert checksum_does_match(output_path, checksums)


def test_checksum_does_match__negative_match_md5(tmpdir):
  output_path = str(tmpdir) + '/tmp.nc'
  checksums = {
    "tmp.nc": {
      "Value": "f83f9ad1718d9b95220ddd6b18dbcecf",
      "Algorithm": "MD5"
    }
  }

  with open(output_path, 'w') as f:
    f.write("This is a different temporary test file\n")

  assert not checksum_does_match(output_path, checksums)


def test_checksum_does_match__positive_match_sha512(tmpdir):
  output_path = str(tmpdir) + '/tmp.nc'
  checksums = {
    "tmp.nc": {
      "Value": "3f5bda96115a5d8fcbcbd71bc28ade2de24bba5f48ce485012f933c877d279d78be3ad028f69af620325a010ce34bd19be78c8b6bf083b0d523165ede8669483",
      "Algorithm": "SHA512"
    }
  }

  with open(output_path, 'w') as f:
    f.write("This is a temporary test file\n")

  assert checksum_does_match(output_path, checksums)


def test_checksum_does_match__negative_match_sha512(tmpdir):
  output_path = str(tmpdir) + '/tmp.nc'
  checksums = {
    "tmp.nc": {
      "Value": "3f5bda96115a5d8fcbcbd71bc28ade2de24bba5f48ce485012f933c877d279d78be3ad028f69af620325a010ce34bd19be78c8b6bf083b0d523165ede8669483",
      "Algorithm": "SHA512"
    }
  }

  with open(output_path, 'w') as f:
    f.write("This is a different temporary test file\n")

  assert not checksum_does_match(output_path, checksums)


def test_checksum_does_match__with_no_checksum(tmpdir):
  output_path = str(tmpdir) + '/tmp.nc'
  checksums = {
    "tmp.nc": None
  }

  with open(output_path, 'w') as f:
    f.write("This is a temporary test file\n")

  assert not checksum_does_match(output_path, checksums)