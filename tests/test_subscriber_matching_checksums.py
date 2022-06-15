from subscriber.podaac_access import checksum_does_match

def test_checksum_does_match__positive_match_md5(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "28d864459bb7628af122ee854439d143",
            "Algorithm": "MD5"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a temporary test file")

    assert checksum_does_match(output_path, checksums)


def test_checksum_does_match__negative_match_md5(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "28d864459bb7628af122ee854439d143",
            "Algorithm": "MD5"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a different temporary test file")

    assert not checksum_does_match(output_path, checksums)


def test_checksum_does_match__positive_match_sha512(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "439de7997fe599d7af6d108534cae418ac95f70f614e3c2fda7a26b03e599211ffbfc85eede5dd933aa7a3c5cfe87d6b3de30ab2d9b4fd45162a5e22b71fffe8",
            "Algorithm": "SHA-512"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a temporary test file")

    assert checksum_does_match(output_path, checksums)


def test_checksum_does_match__negative_match_sha512(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "439de7997fe599d7af6d108534cae418ac95f70f614e3c2fda7a26b03e599211ffbfc85eede5dd933aa7a3c5cfe87d6b3de30ab2d9b4fd45162a5e22b71fffe8",
            "Algorithm": "SHA-512"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a different temporary test file")

    assert not checksum_does_match(output_path, checksums)


def test_checksum_does_match__positive_match_sha256(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "020b00190141a585d214454e3c1c676eaaab12f10c2cb0bf266a0bdb47a78609",
            "Algorithm": "SHA-256"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a temporary test file")

    assert checksum_does_match(output_path, checksums)


def test_checksum_does_match__negative_match_sha256(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": {
            "Value": "020b00190141a585d214454e3c1c676eaaab12f10c2cb0bf266a0bdb47a78609",
            "Algorithm": "SHA-256"
        }
    }

    with open(output_path, 'w') as f:
        f.write("This is a different temporary test file")

    assert not checksum_does_match(output_path, checksums)


def test_checksum_does_match__with_no_checksum(tmpdir):
    output_path = str(tmpdir) + '/tmp.nc'
    checksums = {
        "tmp.nc": None
    }

    with open(output_path, 'w') as f:
        f.write("This is a temporary test file\n")

    assert not checksum_does_match(output_path, checksums)
