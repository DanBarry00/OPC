#!/usr/bin/env python3
"""Read PM1.0 / PM2.5 / PM10 (ug/m3) from a DFRobot HK-A5 ("PM-A5") laser PM sensor.

Frame format (HK-A5 datasheet): 9600 8N1, fixed 32-byte packet,
header 0x42 0x4D, 16-bit big-endian words, checksum = sum of bytes 0..29.
PM values live in data words 1-3 (bytes 4-9). Words 4-6 (bytes 10-15) are reserved.
"""

import serial

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

PORT = "/dev/sensor_3_4"


def read_frame(ser):
    while True:
        if ser.read(1) != b"\x42":           # start symbol 1
            continue
        if ser.read(1) != b"\x4d":           # start symbol 2
            continue
        frame = b"\x42\x4d" + ser.read(30)
        if len(frame) == 32 and sum(frame[:30]) == (frame[30] << 8 | frame[31]):
            return frame

try:
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    client.loop_start()
    with serial.Serial(PORT, 9600, timeout=2) as ser:
        while True:
            f = read_frame(ser)
            pm1  = f[4] << 8 | f[5]
            pm25 = f[6] << 8 | f[7]
            pm10 = f[8] << 8 | f[9]
            payload = {
                "Time": datetime.now().isoformat().replace("T", " ").split(".")[0],
                "Sensor": "DFRobot",
                "PMS10": pm10,
                "PMS2.5": pm25,
                "PMS1": pm1
            }
            
            client.publish(mqtt_topic, json.dumps(payload))
            print(f"Published: {payload}")
except serial.SerialException as e:
    print(f"Serial error: {e}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.loop_stop()
    client.disconnect()