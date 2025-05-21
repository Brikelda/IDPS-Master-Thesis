# modules/decision_engine.py
import json
import paho.mqtt.publish as publish

class DecisionEngine:
    def __init__(self, thresholds=None, output_topic="idps/decision"):
        self.thresholds = thresholds or {
            'TANKLEVEL': (2.0, 9.5),
            'OUTPUTFLOW': (0, 500),
            'RESERVETANKVOLUME': (2, 9.5)
        }
        self.output_topic = output_topic

    def decide(self, predictions):
        decisions = {}
        global_decision = "ALLOW"
        for target, value in predictions.items():
            min_val, max_val = self.thresholds.get(target, (None, None))
            if min_val is not None and (value < min_val or value > max_val):
                decisions[target] = "BLOCK"
                global_decision = "BLOCK"
            else:
                decisions[target] = "ALLOW"
        return global_decision, decisions

    def act_on_decision(self, global_decision, decisions, command):
        message = {
            "global_decision": global_decision,
            "decisions": decisions,
            "command": command
        }
        publish.single(self.output_topic, json.dumps(message), hostname="test.mosquitto.org")
        print(f"📤 Published decision: {global_decision}")


