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
    print(f"connect: {reason_code}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.connect(HOST, PORT, 60)
client.loop_start()
info = client.publish(TOPIC, "hello from publish.py", qos=1)
info.wait_for_publish()
print(f"published to {TOPIC}")
client.loop_stop()
client.disconnect()