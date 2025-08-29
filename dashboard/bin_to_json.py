import os
from datetime import datetime
import time
import sys
from parser import SurtrParser
import json

if len(sys.argv) != 3:
    print("Usage: bin_to_json.py [in file] [out file]")

# Configuration
# init parser
parser = SurtrParser(arg=sys.argv[1])

print("Waiting for parser")

while not parser.stopped():
    time.sleep(0.1)

f = open(sys.argv[2], "w")
json.dump(parser.data, f)
print("Data written to JSON.")