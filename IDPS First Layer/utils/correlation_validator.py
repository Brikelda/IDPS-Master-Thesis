# import pandas as pd
# def validate_anomaly(sensor, current_data, correlation_map, epsilon=0.05):
#     df = pd.read_excel("Data with attacks.xlsx") 
#     if sensor not in correlation_map:
#         return "cyberattack"
#     correlated = correlation_map[sensor]
#     total, consistent = 0, 0
#     for neighbor, corr in correlated.items():
#         if neighbor not in current_data:
#             continue
#         total += 1
#         s_val = current_data[sensor]
#         n_val = current_data[neighbor]
#         if (corr > 0 and abs(s_val - n_val) < epsilon * abs(s_val)) or \
#            (corr < 0 and abs(s_val + n_val) < epsilon * abs(s_val)):
#             consistent += 1
#     return "cyberattack" if total == 0 or consistent / total >= 0.5 else "sensor_fault"


def validate_anomaly(sensor, current_data, epsilon=0.05):
    pump_keys = ['FLOW.PUMP1', 'FLOW.PUMP2', 'FLOW.PUMP3', 'FLOW.PUMP4']

    for pump in pump_keys:
        if pump in current_data:
            if current_data[pump] != 250:
                return "cyberattack"
    return "sensor_fault"
