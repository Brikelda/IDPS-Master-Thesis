import time
import joblib
from xgboost import XGBClassifier
from utils.aeed import load_AEED
from utils.correlation_validator import validate_anomaly
from utils.mqtt_publisher import publish_alert, publish_state
from modbus_sniffer import start_sniffing_in_background, latest_state
import json
import pandas as pd

# === Load Models and Resources ===
model = joblib.load("model/xgboost_attack_detector_areal.pkl")
scaler = joblib.load("model/xgboost_scaler_areal.pkl")
aeed = load_AEED("model/autoencoder_areal.json", "model/autoencoder_areal.h5")

# Feature list (you should load from consistent source)
features = [
    'CONSUMERFLOW.DEFECT', 'CONSUMERFLOW', 'DEFECT.PUMP1', 'DEFECT.PUMP2', 'DEFECT.PUMP3', 'DEFECT.PUMP4',
    'ENTRYFLOW.DEFECT', 'ENTRYFLOW', 'FLOW.PUMP1', 'FLOW.PUMP2', 'FLOW.PUMP3', 'FLOW.PUMP4',
    'INPUTVALVE.CLOSE', 'INPUTVALVE.DEFECT.OPEN', 'INPUTVALVE.FDC.CLOSE', 'INPUTVALVE.FDC.OPEN', 'INPUTVALVE.OPEN',
    'OUTPUTFLOW.DEFECT', 'OUTPUTFLOW', 'OUTPUTVALVE.CLOSE', 'OUTPUTVALVE.DEFECT.OPEN',
    'OUTPUTVALVE.FDC.CLOSE', 'OUTPUTVALVE.FDC.OPEN', 'OUTPUTVALVE.OPEN', 'RESERVETANKVOLUME.DEFECT',
    'RESERVETANKVOLUME', 'STATE.PUMP1', 'STATE.PUMP2', 'STATE.PUMP3', 'STATE.PUMP4', 'TANKLEVEL.DEFECT',
    'TANKLEVEL.HIGH', 'TANKLEVEL.LOW', 'TANKLEVEL', 'CURRENT.FLOW.PUMP1', 'CURRENT.FLOW.PUMP2',
    'CURRENT.FLOW.PUMP3', 'CURRENT.FLOW.PUMP4'
]

# Load correlation map
with open("data/correlation_map_areal_attack_fe.json") as f:
    correlation_map = json.load(f)

# Start Modbus sniffer
start_sniffing_in_background(interface="Ethernet")  # Change if needed
print("🚀 Real-time detection started...")

# Main detection loop
while True:
    # Build live input vector
    raw_input = [latest_state.get(f, 0) for f in features]
    X_scaled = scaler.transform([raw_input])

    # Detection with XGBoost
    if model.predict(X_scaled)[0] == 1:
        # AEED Localization
        _, errors = aeed.predict(pd.DataFrame(X_scaled, columns=features))
        most_suspicious = errors.idxmax(axis=1).iloc[0]
        sensor_val = latest_state.get(most_suspicious, 0)

        # Correlation Validation
        validation = validate_anomaly(most_suspicious, latest_state, correlation_map)

        if validation == "cyberattack":
            print(f"🚨 Attack confirmed at {most_suspicious} = {sensor_val}")
            publish_alert({
                "sensor": most_suspicious,
                "value": float(sensor_val),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "classification": "cyberattack"
            })
        else:
            print(f"⚠️ Sensor fault likely at {most_suspicious} (suppressed)")
    else:
        print("✅ Normal behavior")

    # Publish state for second layer (only model features)
    filtered_state = {k: v for k, v in latest_state.items() if k in features}
    publish_state(filtered_state)

    time.sleep(2)  # Adjust detection interval as needed
