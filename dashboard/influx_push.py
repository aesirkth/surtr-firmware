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
timestamp = '2024-08-25 19:25:00'
url = "http://localhost:8086"
bucket = "Eitr_HT1"
org = "aesir"
token = os.getenv('INFLUX_TOKEN')  # Ensure this environment variable is set

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

# Write data to InfluxDB
for field in parser.data.keys():
    points = []
    for i, value in enumerate(parser.data[field][1]):
        time = base_time + parser.data[field][0][i]
        point = Point(field).field("value", value).time(int(time * 1e9), WritePrecision.NS)
        points.append(point)
        print(i)
    write_api.write(bucket=bucket, org=org, record=points)
    bar.update(1)

print("Data written to InfluxDB.")

# Close the client
client.close()