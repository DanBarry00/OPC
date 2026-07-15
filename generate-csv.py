#!/usr/bin/env python3

import json
import csv
import os
import sys
import signal
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Global state
csv_file = None
csv_writer = None
client = None


def signal_handler(sig, frame):
    print("\nShutting down...")
    if csv_file:
        csv_file.close()
    if client:
        client.loop_stop()
        client.disconnect()
    sys.exit(0)


def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
        return
    
    mqtt_topic = os.getenv("MQTT_TOPIC")
    print(f"Connected to {os.getenv('MQTT_HOST')}:{os.getenv('MQTT_PORT')}")
    client.subscribe(mqtt_topic)
    print(f"Subscribed to {mqtt_topic}")


def on_message(client, userdata, msg):
    global csv_writer, csv_file
    
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        
        required_fields = ['Time', 'Sensor', 'PMS10', 'PMS2.5', 'PMS1']
        if not all(field in payload for field in required_fields):
            print(f"Skipping malformed message: {payload}")
            return
        
        csv_writer.writerow(payload)
        csv_file.flush()
        
        print(f"[{payload['Time']}] {payload['Sensor']}: "
              f"PM10={payload['PMS10']}, PM2.5={payload['PMS2.5']}, PM1={payload['PMS1']}")
    
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {msg.payload}, error: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Unexpected disconnection: {reason_code}")
    else:
        print("Disconnected from broker")


# Load config
load_dotenv()

# Get test name
if len(sys.argv) > 1:
    test_name = sys.argv[1]
else:
    test_name = input("Enter test name: ").strip()
    if not test_name:
        print("Test name cannot be empty.")
        sys.exit(1)

# Setup directory and CSV
tests_dir = Path("tests")
tests_dir.mkdir(exist_ok=True)

csv_path = tests_dir / f"{test_name}.csv"
file_exists = csv_path.exists()

csv_file = open(csv_path, 'a', newline='')
csv_writer = csv.DictWriter(csv_file, fieldnames=['Time', 'Sensor', 'PMS10', 'PMS2.5', 'PMS1'])

if not file_exists:
    csv_writer.writeheader()
    csv_file.flush()
    print(f"Created CSV: {csv_path}")
else:
    print(f"Appending to existing CSV: {csv_path}")

# Setup MQTT
mqtt_host = os.getenv("MQTT_HOST", "localhost")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_user = os.getenv("MQTT_USER")
mqtt_pass = os.getenv("MQTT_PASS")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

if mqtt_user and mqtt_pass:
    client.username_pw_set(mqtt_user, mqtt_pass)

signal.signal(signal.SIGINT, signal_handler)

try:
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    client.loop_forever()
except ConnectionRefusedError:
    print(f"Error: Could not connect to {mqtt_host}:{mqtt_port}")
    sys.exit(1)
finally:
    if csv_file:
        csv_file.close()