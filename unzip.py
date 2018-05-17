import os
import bz2
from bz2 import decompress

data_dir = 'data/xds/historic/BASIC'

for folder, subfolders, files in os.walk(data_dir, 'w'):
    for file_ in files:
        if file_.endswith('.bz2'):
            print("Extracting {0}".format(file_))
            file_path = os.sep.join([folder] + subfolders + [file_])
            zipfile = bz2.BZ2File(file_path) # open the file
            data = zipfile.read() # get the decompressed data
            newfilepath = file_path[:-4] # assuming the filepath ends with .bz2
            open(newfilepath, 'wb').write(data) # write a uncompressed file
