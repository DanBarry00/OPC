#!/usr/bin/env python3

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
mqtt_topic = os.getenv("MQTT_TOPIC", "opc/test")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

if mqtt_user and mqtt_pass:
    client.username_pw_set(mqtt_user, mqtt_pass)

def on_connect(client, userdata, connect_flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}")
        return
    print(f"Connected to {mqtt_host}:{mqtt_port}")

client.on_connect = on_connect

try:
    client.connect(mqtt_host, mqtt_port, keepalive=60)
    client.loop_start()
    
    counter = 0
    while True:
        counter += 1
        payload = {
            "Time": datetime.now().isoformat().replace("T", " ").split(".")[0],
            "Sensor": f"TEST_SENSOR_{counter}",
            "PMS10": 999,
            "PMS2.5": 999,
            "PMS1": 999
        }
        
        client.publish(mqtt_topic, json.dumps(payload))
        print(f"Published: {payload}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down...")
except ConnectionRefusedError:
    print(f"Error: Could not connect to {mqtt_host}:{mqtt_port}")
finally:
    client.loop_stop()
    client.disconnect()