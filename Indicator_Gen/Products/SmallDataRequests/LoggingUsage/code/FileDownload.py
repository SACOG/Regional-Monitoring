# Run from DOS command prompt using python file.py
# cd the directory to folder that contains the log files and hard code path to this .py file

import os
import time

path = "D:\Monitoring\logs"
files = os.listdir(path)
word = '.xlsx' #'GET /monitoring/Data/'

for filelist in files:
    with open("D:\Monitoring\_DownloadedFiles.txt", "a") as file:
        with open(filelist, 'r') as fp:  #This is the log file
            # read all lines in a list
            lines = fp.readlines()
            for line in lines:
                # check if string present on a current line
                if line.find(word) != -1:
                    print(word, 'Exists')
                    parse = line.split()
                    indexVal = len(parse)

                    theDate = parse[0]
                    theFile = parse[4]
                    print(theDate, indexVal)
                    theResult = theDate + " " + theFile
                    file.write(theResult + "\n")
