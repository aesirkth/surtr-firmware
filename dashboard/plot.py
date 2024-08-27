from parser import SurtrParser
import sys
import time
import matplotlib.pyplot as plt

parser = SurtrParser(sys.argv[1])

while True:
    if parser.stopped():
        break
    time.sleep(0.1)

print("generating")

v_start = 0.9
v_end = 4.5
field = "value50"
convert = lambda x: 69 * (x - v_start) / (v_end - v_start)
converted_values = [convert(x) for x in parser.data[field][1]]

plt.scatter(parser.data[field][0], converted_values)
plt.show()