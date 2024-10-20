import os
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from parser import SurtrParser
import time
import sys
import progressbar
from tqdm import tqdm

# Configuration
timestamp = '2024-10-6 16:50:00'
url = "http://localhost:8086"
bucket = "Eitr_HT3"
org = "aesir"
token = os.getenv('INFLUX_TOKEN')  # Ensure this environment variable is set
print(token)
# init parser
parser = SurtrParser(arg=sys.argv[1])

print("Waiting for parser")

while not parser.stopped():
    time.sleep(0.1)

# Initialize the client
client = InfluxDBClient(url=url, token=token, org=org)

# Create or overwrite the bucket
def create_or_overwrite_bucket(client, bucket_name):
    buckets_api = client.buckets_api()
    existing_buckets = buckets_api.find_buckets().buckets
    for bucket in existing_buckets:
        if bucket.name == bucket_name:
            print(f"Bucket '{bucket_name}' already exists. Deleting...")
            buckets_api.delete_bucket(bucket.id)
            break
    # Create new bucket
    print(f"Creating bucket '{bucket_name}'...")
    buckets_api.create_bucket(bucket_name=bucket_name, org=org)
    print(f"Bucket '{bucket_name}' created.")

create_or_overwrite_bucket(client, bucket)

# Initialize the Write API
write_api = client.write_api(write_options=SYNCHRONOUS)

# Parse the timestamp string
format_str = '%Y-%m-%d %H:%M:%S'
parsed_datetime = datetime.strptime(timestamp, format_str)

# Convert parsed datetime to Unix timestamp (seconds)
base_time = parsed_datetime.timestamp()



bar = tqdm(total=len(parser.data.keys()), desc="Uploading to influx")

v_start = 0.9
v_end = 4.5
c_start = 4
c_end = 20

field_to_name = {
    "value50": "m2",
    "value60": "m1",
    "value70": "m3",

    "value80": "e2",
    "value90": "e1",
    "value100": "e3",
    "value110": "e4",
}

# Write data to InfluxDB
for field in parser.data.keys():
    points = []
    if field in ["value50", "value60", "value70"]:
        convert = lambda x: 69 * (x - v_start) / (v_end - v_start)
    elif field in ["value80", "value90"]:
        convert = lambda x: 250 * (x - c_start) / (c_end - c_start)
    elif field in ["value100", "value110"]:
        convert = lambda x: 100 * (x - c_start) / (c_end - c_start)
    else:
        convert = lambda x: x
    for i, value in enumerate(parser.data[field][1]):
        time = base_time + parser.data[field][0][i]
        new_value = convert(value)
        new_field = field
        if field in field_to_name:
            new_field = field_to_name[field]
        point = Point(new_field).field("value", new_value).time(int(time * 1e9), WritePrecision.NS)
        points.append(point)

        if new_value != value:
            point = Point(new_field + "_raw").field("value", value).time(int(time * 1e9), WritePrecision.NS)
            print(new_field + "_raw")
            points.append(point)
        # print(i)
    write_api.write(bucket=bucket, org=org, record=points)
    bar.update(1)

print("Data written to InfluxDB.")

# Close the client
client.close()