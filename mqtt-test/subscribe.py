import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
HOST  = os.getenv("MQTT_HOST", "localhost")
PORT  = int(os.getenv("MQTT_PORT", "1883"))
USER  = os.getenv("MQTT_USER")
PASS  = os.getenv("MQTT_PASS")
TOPIC = os.getenv("MQTT_TOPIC", "opc/test")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"connected; subscribing to {TOPIC}")
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"connect refused: {reason_code}")

def on_message(client, userdata, msg):
    print(f"{msg.topic}  {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.on_message = on_message
client.connect(HOST, PORT, 60)
client.loop_forever()