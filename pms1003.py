#!/usr/bin/env python3

import json
import os
import struct
import time
from datetime import datetime

import serial
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

mqtt_host = os.getenv("MQTT_HOST", "localhost")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_user = os.getenv("MQTT_USER")
mqtt_pass = os.getenv("MQTT_PASS")
mqtt_topic = os.getenv("MQTT_TOPIC", "opc/test")

SENSOR_NAME = "pms1003"
SERIAL_PORT = os.getenv("PMS1003_PORT", "/dev/pms1003")


def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
        return
    print(f"Connected to {mqtt_host}:{mqtt_port}")


def read_loop(client, ser):
    """Read PMS1003 frames and publish each one over MQTT."""
    while True:
        byte1 = ser.read(1)
        if not byte1 or byte1[0] != 0x42:
            continue

        byte2 = ser.read(1)
        if not byte2 or byte2[0] != 0x4d:
            continue

        frame_len_bytes = ser.read(2)
        if len(frame_len_bytes) < 2:
            continue
        frame_len = struct.unpack(">H", frame_len_bytes)[0]

        frame_data = ser.read(frame_len)
        if len(frame_data) != frame_len:
            continue

        # Atmospheric-environment values (Data 4-6). Use [0:2]/[2:4]/[4:6] for CF=1.
        pm1_0_atm = struct.unpack(">H", frame_data[6:8])[0]
        pm2_5_atm = struct.unpack(">H", frame_data[8:10])[0]
        pm10_atm = struct.unpack(">H", frame_data[10:12])[0]

        payload = {
            "Time": datetime.now().isoformat().replace("T", " ").split(".")[0],
            "Sensor": SENSOR_NAME,
            "PMS10": pm10_atm,
            "PMS2.5": pm2_5_atm,
            "PMS1": pm1_0_atm,
        }

        client.publish(mqtt_topic, json.dumps(payload))
        print(f"Published: {payload}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if mqtt_user and mqtt_pass:
        client.username_pw_set(mqtt_user, mqtt_pass)

    client.on_connect = on_connect

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, baudrate=9600, timeout=2)
        client.connect(mqtt_host, mqtt_port, keepalive=60)
        client.loop_start()
        read_loop(client, ser)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {mqtt_host}:{mqtt_port}")
    finally:
        client.loop_stop()
        client.disconnect()
        if ser is not None and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()