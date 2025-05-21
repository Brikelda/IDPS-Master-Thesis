# # simulator_engine.py
# import joblib
# import numpy as np

# class SimulatorEngine:
#     def __init__(self):
#         self.model = joblib.load("xgboost_predictor.pkl")
#         self.features = joblib.load("xgboost_features.pkl")

#     def simulate(self, current_state: dict, command: dict):
#         # Merge command into the state
#         simulated_input = current_state.copy()
#         simulated_input.update(command)

#         # Reorder and fill any missing features
#         input_vector = []
#         for feature in self.features:
#             value = simulated_input.get(feature, 0.0)
#             input_vector.append(value)

#         # Predict outcome (e.g., next tank level)
#         input_array = np.array(input_vector).reshape(1, -1)
#         prediction = self.model.predict(input_array)[0]
#         return prediction



# simulator_engine.py

# simulator_engine.py

import joblib
import time
from xgboost import XGBRegressor


class SimulatorEngineBase:
    def predict(self, system_state, intercepted_command):
        raise NotImplementedError

    def predict_batch(self, system_state, list_of_commands):
        latencies = []
        all_preds = []
        for cmd in list_of_commands:
            preds, lat = self.predict(system_state, cmd)
            latencies.append(lat)
            all_preds.append(preds)
        return all_preds, latencies


class MultiModelSimulator(SimulatorEngineBase):
    def __init__(self, model_paths, feature_paths):
        # Load models using XGBoost's native format
        self.models = {}
        for target, path in model_paths.items():
            model = XGBRegressor()
            model.load_model(path)
            self.models[target] = model

        # Load feature lists as before
        self.features = {k: joblib.load(v) for k, v in feature_paths.items()}

    def predict(self, system_state, intercepted_command):
        input_data = {**system_state, **intercepted_command}
        predictions = {}
        start = time.perf_counter()
        for target in self.models:
            feats = self.features[target]
            X = [input_data.get(f, 0) for f in feats]
            pred = self.models[target].predict([X])[0]
            predictions[target] = pred
        latency = time.perf_counter() - start
        return predictions, latency


    
    # def debug_print_features(self, system_state, intercepted_command):
    #     input_data = {**system_state, **intercepted_command}

    #     for target in self.models:
    #         expected_features = self.features[target]

    #         print(f"\n[DEBUG] Target: {target}")
    #         print(f"[DEBUG] Expected features ({len(expected_features)}): {expected_features}")
    #         print(f"[DEBUG] Received input keys ({len(input_data.keys())}): {list(input_data.keys())}")


# class RetrainingSimulator(SimulatorEngineBase):
#     def __init__(self, df, sensor_cols):
#         self.df = df
#         self.sensor_cols = sensor_cols

#     def predict(self, system_state, intercepted_command):
#         input_data = {**system_state, **intercepted_command}


#         predictions = {}
#         start = time.perf_counter()
#         for target in ['TANKLEVEL', 'OUTPUTFLOW', 'RESERVETANKVOLUME']:
#             df_temp = self.df.copy()
#             df_temp[f"{target}_next"] = df_temp[target].shift(-1)
#             df_temp.dropna(inplace=True)

#             X = df_temp[self.sensor_cols]
#             y = df_temp[f"{target}_next"]

#             scaler = MinMaxScaler().fit(X)
#             X_scaled = scaler.transform(X)

#             model = XGBRegressor(n_estimators=100).fit(X_scaled, y)

#             X_input = [input_data.get(f, 0) for f in self.sensor_cols]
#             pred = model.predict([X_input])[0]
#             predictions[target] = pred
#         latency = time.perf_counter() - start
#         return predictions, latency

# class RFMultiOutputSimulator(SimulatorEngineBase):
#     def __init__(self, model_path, feature_path, targets):
#         self.model = joblib.load(model_path)
#         self.features = joblib.load(feature_path)
#         self.targets = targets

#     def predict(self, system_state, intercepted_command):
#         input_data = {**system_state, **intercepted_command}
#         X = [input_data.get(f, 0) for f in self.features]
#         start = time.perf_counter()
#         preds = self.model.predict([X])[0]
#         latency = time.perf_counter() - start
#         return dict(zip(self.targets, preds)), latency
