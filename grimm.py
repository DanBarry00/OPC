#!/usr/bin/env python3

import json
import serial
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv()

mqtt_host = os.getenv("MQTT_HOST", "localhost")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_user = os.getenv("MQTT_USER")
mqtt_pass = os.getenv("MQTT_PASS")
mqtt_topic = os.getenv("MQTT_TOPIC")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

if mqtt_user and mqtt_pass:
    client.username_pw_set(mqtt_user, mqtt_pass)

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
        return
    print(f"Connected to {mqtt_host}:{mqtt_port}")

client.on_connect = on_connect

PORT = "/dev/GRIMM"
BAUD = 9600

print(f"Connecting to {PORT} at {BAUD} baud...")
with serial.Serial(PORT, BAUD, timeout=2) as ser:
    # Check version
    print("Checking firmware version...")
    ser.write(b"v\r")
    time.sleep(1)
    version_response = ser.read(300).decode(errors="ignore").strip()
    print(f"Response: {version_response}\n")
    
    if "7.80" not in version_response:
        print("ERROR: Not version 7.80. Exiting.")
        exit(1)
    
    print("✓ Version 7.80 detected. Reading particle sizes...\n")
    print("ID\t\tPM1.0\t\tPM2.5\t\tPM10")
    print("-" * 50)
    
    try:
        client.connect(mqtt_host, mqtt_port, keepalive=60)
        client.loop_start()
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {mqtt_host}:{mqtt_port}")
        exit(1)
    
    try:
        while True:
            try:
                line = ser.readline().decode("ascii").strip()
                
                if not line or len(line) < 4:
                    continue
                
                values = [v for v in line.split() if v]
                
                # Skip status messages and incomplete lines
                if values[0].upper() == 'P' or len(values) < 4:
                    continue
                
                # Parse N-lines using grimm.py ordering
                line_id = values[0]
                pm10 = values[1]   # PM10
                pm25 = values[2]   # PM2.5
                pm1 = values[3]    # PM1.0
                
                print(f"{line_id}\t\t{pm1}\t\t{pm25}\t\t{pm10}")
                
                payload = {
                    "Time": datetime.now().isoformat().replace("T", " ").split(".")[0],
                    "Sensor": "GRIMM",
                    "PMS10": float(pm10),
                    "PMS2.5": float(pm25),
                    "PMS1": float(pm1)
                }
                
                client.publish(mqtt_topic, json.dumps(payload))
                
            except (UnicodeDecodeError, ValueError, IndexError) as e:
                continue
            except KeyboardInterrupt:
                print("\n\nStopped.")
                break
    finally:
        client.loop_stop()
        client.disconnect()