from parser import SurtrParser
import sys
import time
import matplotlib.pyplot as plt

print("parsing...")

parser = SurtrParser(sys.argv[1])

while True:
    if parser.stopped():
        break
    time.sleep(0.1)

print("generating...")

data = {
    "m2": {
        "start": 0.9,
        "end": 4.5,
        "scaler": 69,
        "field": "value50",
        "data_series": [],
        "time_series": []
    },
    "m1": {
        "start": 0.9,
        "end": 4.5,
        "scaler": 69,
        "field": "value60",
        "data_series": [],
        "time_series": []
    },
    "m3": {
        "start": 0.9,
        "end": 4.5,
        "scaler": 69,
        "field": "value70",
        "data_series": [],
        "time_series": []
    },
    "e2": {
        "start": 4,
        "end": 20,
        "scaler": 250,
        "field": "value80",
        "data_series": [],
        "time_series": []
    },
    "e1": {
        "start": 4,
        "end": 20,
        "scaler": 250,
        "field": "value90",
        "data_series": [],
        "time_series": []
    },
    "e3": {
        "start": 4,
        "end": 20,
        "scaler": 100,
        "field": "value100",
        "data_series": [],
        "time_series": []
    },
    "e4": {
        "start": 4,
        "end": 20,
        "scaler": 100,
        "field": "value110",
        "data_series": [],
        "time_series": []
    },

}

for series in data.values():
    series["data_series"] = [series["scaler"] * (x - series["start"]) / (series["end"] - series["start"]) for x in parser.data[series["field"]][1]]

    series["time_series"] = [0] * len(parser.data[series["field"]][0])
    # seems to be an overflow in the time counting so try to unfold the data by detecting if the time goes backwards
    overflow_value = 0
    for i in range(1, len(parser.data[series["field"]][0])):
        if parser.data[series["field"]][0][i - 1] > parser.data[series["field"]][0][i]:
            overflow_value += series["time_series"][i - 1]
            print(f"time overflow at {overflow_value}")
        series["time_series"][i] = parser.data[series["field"]][0][i] + overflow_value 

plt.subplot(1, 2, 1)
plt.plot(data["m2"]["time_series"], data["m2"]["data_series"])
plt.plot(data["m1"]["time_series"], data["m1"]["data_series"])
plt.plot(data["m3"]["time_series"], data["m3"]["data_series"])

plt.subplot(1, 2, 2)
plt.plot(data["e2"]["time_series"], data["e2"]["data_series"])
plt.plot(data["e1"]["time_series"], data["e1"]["data_series"])
plt.plot(data["e3"]["time_series"], data["e3"]["data_series"])
plt.plot(data["e4"]["time_series"], data["e4"]["data_series"])
plt.show()