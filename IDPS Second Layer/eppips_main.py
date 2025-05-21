# # eppips_main.py
# # Entry point for second layer, triggered on anomalies and returns to sleep when system is safe

# import time
# from modules.event_receiver import EventReceiver
# from modules.state_collector import StateCollector
# from modules.command_interceptor import CommandInterceptor
# from modules.simulator_engine import SimulatorEngine
# from modules.decision_engine import DecisionEngine

# # === Initialize modules ===
# event_receiver = EventReceiver()
# state_collector = StateCollector()
# command_interceptor = CommandInterceptor()
# simulator = SimulatorEngine()
# decider = DecisionEngine()

# # === Define internal state ===
# last_alert_time = None
# cooldown_start = None
# ACTIVE = False
# COOLDOWN_PERIOD = 120  # seconds


# def handle_anomaly(anomaly):
#     global last_alert_time, ACTIVE, cooldown_start

#     print("\n🚨 Anomaly Received:", anomaly)
#     last_alert_time = time.time()
#     cooldown_start = None
#     ACTIVE = True

#     # 1. Get current system state
#     current_state = state_collector.collect()
#     print("📡 System State Collected")

#     # 2. Intercept pending command
#     command = command_interceptor.get_pending_command()
#     print("📥 Intercepted Command:", command)

#     # 3. Predict outcome
#     predicted_value = simulator.simulate(current_state, command)
#     print(f"🔮 Predicted Output: {predicted_value:.3f}")

#     # 4. Make decision
#     decision = decider.decide(predicted_value)
#     print(f"🧠 Decision: {decision}")

#     # 5. Act on decision
#     decider.act_on_decision(decision, command)


# def handle_state_update(state_msg):
#     state_collector.update_state(state_msg)


# def check_safe_to_sleep():
#     global last_alert_time, ACTIVE, cooldown_start

#     if not ACTIVE:
#         return False

#     now = time.time()

#     # If cooldown hasn't started yet, check if alert timeout has passed
#     if cooldown_start is None and last_alert_time and (now - last_alert_time) > COOLDOWN_PERIOD:
#         print("🧊 Cooldown started... Monitoring stability")
#         cooldown_start = now
#         return False

#     # If already in cooldown, check if system remains stable
#     if cooldown_start:
#         stable_state = state_collector.check_stability()
#         #no_pending_threats = command_interceptor.buffer_clear()
#         no_pending_threats = True


#         if (now - cooldown_start) > COOLDOWN_PERIOD and stable_state and no_pending_threats:
#             print("😴 System stabilized. Second layer going back to sleep.")
#             ACTIVE = False
#             cooldown_start = None
#             last_alert_time = None
#             return True

#     return False


# # === Start anomaly listener ===
# event_receiver.start_listening(callback=handle_anomaly, state_callback=handle_state_update)

# # === Background monitor loop ===
# while True:
#     if ACTIVE:
#         check_safe_to_sleep()
#     time.sleep(5)




# eppips_main.py
# Entry point for second layer, triggered on anomalies and returns to sleep when system is safe

import time
from modules.event_receiver import EventReceiver
from modules.state_collector import StateCollector
from modules.command_interceptor import get_pending_command 
from modules.simulator_engine import MultiModelSimulator, RetrainingSimulator, RFMultiOutputSimulator
from modules.decision_engine import DecisionEngine
from codecarbon import EmissionsTracker
import numpy as np


# === CONFIG ===
# scenario = "retrain"  # options: "multi", "retrain", "rf"

# === Initialize modules ===
event_receiver = EventReceiver()
state_collector = StateCollector()
decider = DecisionEngine()

# Dummy example system state for testing
# system_state = {
#     'L_T1': 2.1, 'L_T2': 2.3, 'P_J280': 0.8, 'F_PU1': 250
#     # add more real values if needed
# }

# Initialize simulator depending on scenario


sim = MultiModelSimulator(
    model_paths={
        'TANKLEVEL': "xgb_model_tanklevel.pkl",
        'OUTPUTFLOW': "xgb_model_outputflow.pkl",
        'RESERVETANKVOLUME': "xgb_model_reservetankvolume.pkl"
    },
    feature_paths={
        'TANKLEVEL': "xgb_features_tanklevel.pkl",
        'OUTPUTFLOW': "xgb_features_outputflow.pkl",
        'RESERVETANKVOLUME': "xgb_features_reservetankvolume.pkl"
    }
)

# if scenario == "multi":
#     model_paths = {
#         "TANKLEVEL": "xgb_model_tanklevel.pkl",
#         "OUTPUTFLOW": "xgb_model_outputflow.pkl",
#         "RESERVETANKVOLUME": "xgb_model_reservetankvolume.pkl"
#     }
#     feature_paths = {
#         "TANKLEVEL": "xgb_features_tanklevel.pkl",
#         "OUTPUTFLOW": "xgb_features_outputflow.pkl",
#         "RESERVETANKVOLUME": "xgb_features_reservetankvolume.pkl"
#     }
#     simulator = MultiModelSimulator(model_paths, feature_paths)

# elif scenario == "retrain":
#     import pandas as pd
#     df_attack_data = pd.read_excel("Data with attacks.xlsx")
#     sensor_cols = [col for col in df_attack_data.columns if col not in ['Date', 'Hours', 'ATT_FLAG']]
#     simulator = RetrainingSimulator(df_attack_data, sensor_cols)

# elif scenario == "rf":
#     simulator = RFMultiOutputSimulator("rf_multi_model.pkl", "rf_multi_features.pkl",
#                                        ['TANKLEVEL', 'OUTPUTFLOW', 'RESERVETANKVOLUME'])
# else:
#     raise ValueError(f"Unknown scenario: {scenario}")

last_alert_time = None
cooldown_start = None
ACTIVE = False
COOLDOWN_PERIOD = 120  # seconds

# tracker = EmissionsTracker(
#     project_name=f"IDPS_{scenario}",
#     output_file="emissions.csv",
#     output_dir=".",
#     measure_power_secs=1,     # log every second
#     save_to_file=True,
#     tracking_mode="machine",
#     log_level="info"
# )


def handle_anomaly(anomaly):
    global last_alert_time, ACTIVE, cooldown_start

    print("\n🚨 Anomaly Received:", anomaly)
    last_alert_time = time.time()
    cooldown_start = None
    ACTIVE = True

    # 1. Get current system state
    current_state = state_collector.collect()
    print("📡 System State Collected")

    # 2. Get dummy intercepted commands
    dummy_commands = get_pending_command()

    # # === START energy tracking ===
    # tracker = EmissionsTracker(project_name=f"IDPS_{scenario}")
    # tracker.start()

    # 3. Run batch prediction
    predictions, latencies = sim.predict_batch(current_state, dummy_commands)

    # === STOP energy tracking ===
    # emissions = tracker.stop()

    # 4. Print per command
    for i, (pred, lat) in enumerate(zip(predictions, latencies)):
        print(f"\n🔍 Command {i + 1}: {dummy_commands[i]}")
        print(f"→ Predictions: {pred}")
        print(f"⏱️  Latency: {lat:.4f} sec")

    # 5. Summary
    print("\n=== Batch Summary ===")
    print(f"Total commands: {len(dummy_commands)}")
    print(f"Average latency: {np.mean(latencies):.4f} sec")
    print(f"Std dev latency: {np.std(latencies):.4f} sec")
    print(f"Total time: {np.sum(latencies):.4f} sec")
    # print(f"🌍 Energy consumed for prediction: {emissions:.8f} kgCO2eq")

    # 6. Act on predictions
    for pred in predictions:
        for target, predicted_value in pred.items():
            decision = decider.decide(predicted_value)
            print(f"🧠 Decision for {target}: {decision}")


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
        no_pending_threats = True  # for now assume no command buffer
        if (now - cooldown_start) > COOLDOWN_PERIOD and stable_state and no_pending_threats:
            print("😴 System stabilized. Second layer going back to sleep.")
            ACTIVE = False
            cooldown_start = None
            last_alert_time = None
            return True

    return False

# === Start anomaly listener ===

# tracker.start()

event_receiver.start_listening(callback=handle_anomaly, state_callback=handle_state_update)

# === Background monitor loop ===
# try:
while True:
    if ACTIVE:
        check_safe_to_sleep()
    time.sleep(5)
# finally:
#     emissions = tracker.stop()
#     print(f"🌍 Energy consumption for scenario '{scenario}': {emissions:.6f} kgCO2eq")

    

