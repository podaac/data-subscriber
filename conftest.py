# A hack to force the inclusion of the 'subscriber' moduls for pytest
import sys, os
sys.path.append(os.getcwd()+"/subscriber")
