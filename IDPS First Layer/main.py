import pandas as pd
import joblib
import json
from utils.aeed import load_AEED
from utils.correlation_validator import validate_anomaly
from utils.mqtt_publisher import publish_alert, publish_state
import time

# Load models
xgb = joblib.load("model/xgboost_attack_detector_areal.pkl")
aeed = load_AEED("model/autoencoder_areal.json", "model/autoencoder_areal.h5")
scaler = joblib.load("model/xgboost_scaler_areal.pkl")

# Load correlation map
with open("data/correlation_map_areal_attack_fe.json") as f:
    correlation_map = json.load(f)

# For testing: read one sample at a time
df = pd.read_excel("Data with attacks.xlsx")  # Or replace with streaming
sensor_cols = [col for col in df.columns if col not in ['Date','Hours','ATT_FLAG']]

for i, row in df.iloc[270:].iterrows():
    X_raw = pd.DataFrame([row[sensor_cols]])
    X_scaled = pd.DataFrame(scaler.transform(X_raw), columns=sensor_cols)

    # XGBoost detection
    if xgb.predict(X_scaled)[0] == 1:
        # AEED localization
        _, errors = aeed.predict(X_scaled)
        most_suspicious = errors.idxmax(axis=1).iloc[0]
        sensor_val = X_raw[most_suspicious].values[0]

        # Correlation validation
        validation = validate_anomaly(most_suspicious, row.to_dict(), correlation_map)

        if validation == "cyberattack":
            print(f"🚨 Attack confirmed at {most_suspicious} = {sensor_val}")
            publish_alert({
                "sensor": most_suspicious,
                "value": float(sensor_val),
                "timestamp": f"{row['Date']} {row['Hours']}:00",
                "classification": "cyberattack"
            })
        else:
            print(f"⚠️ Sensor fault likely at {most_suspicious} (suppressed)")
    
    else:
        print(f"✅ Normal behavior at {row['Date']} {row['Hours']}:00")
        
    # Publish system state for second layer
    publish_state(row[sensor_cols].to_dict())

    time.sleep(1)
