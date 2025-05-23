# eppips_main.py — Entry point for second layer of the IDPS

import time
import numpy as np
from modules.event_receiver import EventReceiver
from modules.state_collector import StateCollector
from modules.command_interceptor import get_pending_command 
from modules.simulator_engine import MultiModelSimulator
from modules.decision_engine import DecisionEngine

# === Initialize modules ===
event_receiver = EventReceiver()
state_collector = StateCollector()
decider = DecisionEngine()

# Load trained multi-model XGBoost simulator
sim = MultiModelSimulator(
    model_paths={
        'TANKLEVEL': "xgb_model_tanklevel.json",
        'OUTPUTFLOW': "xgb_model_outputflow.json",
        'RESERVETANKVOLUME': "xgb_model_reservetankvolume.json"
    },

    feature_paths={
        'TANKLEVEL': "xgb_features_tanklevel.pkl",
        'OUTPUTFLOW': "xgb_features_outputflow.pkl",
        'RESERVETANKVOLUME': "xgb_features_reservetankvolume.pkl"
    }
)

# === Internal control state ===
last_alert_time = None
cooldown_start = None
ACTIVE = False
COOLDOWN_PERIOD = 120  # seconds


def handle_anomaly(anomaly):
    global last_alert_time, ACTIVE, cooldown_start

    print("\n🚨 Anomaly Received:", anomaly)
    last_alert_time = time.time()
    cooldown_start = None
    ACTIVE = True

    # 1. Get current system state
    current_state = state_collector.collect()
    print("📡 System State Collected")

    # 2. Get intercepted commands (simulate batch of commands)
    pending_commands = get_pending_command()

    # 3. Run predictions
    predictions, latencies = sim.predict_batch(current_state, pending_commands)

    # 4. Report
    for i, (pred, lat) in enumerate(zip(predictions, latencies)):
        print(f"\n🔍 Command {i + 1}: {pending_commands[i]}")
        print(f"→ Predictions: {pred}")
        print(f"⏱️  Latency: {lat:.4f} sec")
    
    print("\n=== Batch Summary ===")
    print(f"Total commands: {len(pending_commands)}")
    print(f"Average latency: {np.mean(latencies):.4f} sec")
    print(f"Std dev latency: {np.std(latencies):.4f} sec")
    print(f"Total time: {np.sum(latencies):.4f} sec")

    # 5. Act on decisions
    for i, pred in enumerate(predictions):
        global_decision, decisions = decider.decide(pred)
        print(f"🧠 Global Decision: {global_decision} | Breakdown: {decisions}")
        decider.act_on_decision(global_decision, decisions, pending_commands[i])


def handle_state_update(state_msg):
    state_collector.update_state(state_msg)


def check_safe_to_sleep():
    global last_alert_time, ACTIVE, cooldown_start

    if not ACTIVE:
        return False

    now = time.time()

    if cooldown_start is None and last_alert_time and (now - last_alert_time) > COOLDOWN_PERIOD:
        print("🧊 Cooldown started... Monitoring stability")
        cooldown_start = now
        return False

    if cooldown_start:
        stable_state = state_collector.check_stability()
        no_pending_threats = True  # assume clear buffer for now

        if (now - cooldown_start) > COOLDOWN_PERIOD and stable_state and no_pending_threats:
            print("😴 System stabilized. Second layer going back to sleep.")
            ACTIVE = False
            cooldown_start = None
            last_alert_time = None
            return True

    return False


# === Start MQTT listener ===
event_receiver.start_listening(callback=handle_anomaly, state_callback=handle_state_update)

# === Background monitor loop ===
while True:
    if ACTIVE:
        check_safe_to_sleep()
    time.sleep(5)

