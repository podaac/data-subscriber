from subscriber import podaac_data_subscriber as pds
from datetime import datetime
import os
from os.path import exists
import argparse
import shutil
import tempfile
import subprocess
import unittest
from unittest.mock import patch

class TestPDS(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.test_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        # Remove a temporary directory
        shutil.rmtree(self.temp_dir)

    def test_validate(self):
        #work
        a = self.validate(["-c", "viirs", "-d", "/data"])
        assert a.dataSince  == False
        assert a.collection == "viirs"
        assert a.outputDirectory == "/data"

        a = self.validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90"])
        assert a.bbox == "-180,-90,180,90"

        a = self.validate(["-c", "viirs", "-d", "/data", "-b=-170,-80,170,20"])
        assert a.bbox == "-170,-80,170,20"

        a = self.validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-ds", "2021-01-01T00:00:00Z"])
        assert a.dataSince == "2021-01-01T00:00:00Z"

        a = self.validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-m","100"])
        assert a.minutes == 100, "should equal 100"

        a = self.validate(["-c", "viirs", "-d", "/data", "-b=-180,-90,180,90", "-e", ".txt", ".nc"])
        assert ".txt" in a.extensions
        assert ".nc" in a.extensions

        #don't work
        # with pytest.raises(SystemExit):
        #     a = self.validate([])

        #don't work
        # with pytest.raises(SystemExit):
        #     a = self.validate(["-c", "viirs"])
        #
        # with pytest.raises(SystemExit):
        #     a = self.validate(["-d", "/data"])
        #
        # with pytest.raises(ValueError):
        #     a = self.validate(["-c", "viirs", "-d", "/data", "-ds", "2021-01-01T00:00:Z"])
        #
        # with pytest.raises(ValueError):
        #     a = self.validate(["-c", "viirs", "-d", "/data", "-b=-170abc,-80,170,20"])
        #
        # with pytest.raises(SystemExit):
        #     a = self.validate(["-c", "viirs", "-d", "/data", "-m","60b"])

    def test_directory_outputs(self):
        time_now = datetime.utcnow()
        year = time_now.strftime('%Y')
        month = time_now.strftime('%m')
        day = time_now.strftime('%d')
        day_of_year = time_now.strftime('%j')

        a = self.validate(["-c", "VIIRS_N20-OSPO-L2P-v2.61", "-dydoy", "-e", ".nc", "-m", "60", "-b=-180,-90,180,90"])
        assert a.dataSince == False
        assert a.collection == "VIIRS_N20-OSPO-L2P-v2.61"
        assert a.outputDirectory == None
        assert a.dydoy == True
        assert a.bbox == "-180,-90,180,90"

    # work in progress
    # @patch('subscriber.podaac_data_subscriber.urllib.request.urlretrieve')
    @patch('argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(collection="VIIRS_N20-OSPO-L2P-v2.61", dydoy=True, extensions=".nc", minutes="30", version=True, bbox="-180,-90,180,90"))
    def test_process(self, mock_arg):
        os.chdir(self.temp_dir)
        # result = subprocess.run([self.test_path + '/subscriber/podaac_data_subscriber.py', "-c", "VIIRS_N20-OSPO-L2P-v2.61", "-dydoy", "-e", ".nc", "-m", "30", "-b=-180,-90,180,90"], capture_output=True)
        print(mock_arg)
        output = pds.run()
        # result = subprocess.run(['pwd'], capture_output=True, shell=True)
        print(output)
        # print(mock_urllib)
        # print(result)
        # print(result.stdout)

    def validate(self, args):
        parser = pds.create_parser()
        args2 = parser.parse_args(args)
        pds.validate(args2)
        return args2


if __name__ == '__main__':
    unittest.main()
