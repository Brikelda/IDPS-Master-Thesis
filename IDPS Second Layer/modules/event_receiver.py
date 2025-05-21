# event_receiver.py (updated to subscribe to both alerts and state topics)
import paho.mqtt.client as mqtt
import json
import threading

class EventReceiver:
    def __init__(self):
        print("🛠️ EventReceiver initialized")  # Add this
        self.client = mqtt.Client()
        self.alert_callback = None
        self.state_callback = None

     
    def __init__(self):
        self.client = mqtt.Client()
        self.alert_callback = None
        self.state_callback = None

    def start_listening(self, callback, state_callback=None):
        print("📡 start_listening called")

        self.alert_callback = callback
        self.state_callback = state_callback
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            print("🔌 Attempting to connect to MQTT broker...")
            self.client.connect("broker.hivemq.com", 1883, 60)
            print("✅ connect() call succeeded")
        except Exception as e:
            print(f"❌ MQTT connection failed: {e}")
            return

        thread = threading.Thread(target=self.client.loop_forever)
        thread.start()
        print("🧵 MQTT listening thread started")


    def on_connect(self, client, userdata, flags, rc):
        print("🔌 Connected to MQTT broker")
        self.client.subscribe("wds/alerts")
        self.client.subscribe("wds/state")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == "wds/alerts" and self.alert_callback:
                self.alert_callback(payload)
            elif msg.topic == "wds/state" and self.state_callback:
                self.state_callback(payload)
        except Exception as e:
            print(f"⚠️ Error handling message: {e}")

