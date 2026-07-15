#!/usr/bin/env python3
import serial
import struct

import json
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

PORT = "/dev/sensor_3_1"

ser = serial.Serial(PORT, 9600, timeout=2)

try:
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    client.loop_start()
    while True:
        # sync to start bytes 0x42 0x4D
        if ser.read(1) != b"\x42":
            continue
        if ser.read(1) != b"\x4D":
            continue

        body = ser.read(30)              # frame_len(2) + 13 data words(26) + checksum(2)
        if len(body) != 30:
            continue

        if (0x42 + 0x4D + sum(body[:28])) != struct.unpack(">H", body[28:30])[0]:
            continue                     # checksum mismatch -> drop frame

        f = struct.unpack(">14H", body[:28])
        # f[1:4] = PM1.0/2.5/10 (CF=1, "standard")  |  f[4:7] = PM1.0/2.5/10 (atmospheric)
        pm1, pm25, pm10 = f[4], f[5], f[6]

        payload = {
            "Time": datetime.now().isoformat().replace("T", " ").split(".")[0],
            "Sensor": f"PMS6003",
            "PMS10": pm10,
            "PMS2.5": pm25,
            "PMS1": pm1
        }
        client.publish(mqtt_topic, json.dumps(payload))
        print(f"Published: {payload}")
        
except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"Error: {e}")
finally:
    ser.close()
    client.loop_stop()
    client.disconnect()