import paho.mqtt.client as mqtt
import json

client = mqtt.Client()
client.connect("broker.hivemq.com", 1883, 60)

def publish_alert(alert):
    payload = json.dumps(alert)
    client.publish("wds/alerts", payload)
    print(f"📡 Published Alert: {payload}")

def publish_state(state):
    payload = json.dumps(state)
    client.publish("wds/state", payload)
    print(f"📡 Published State: {payload}")
