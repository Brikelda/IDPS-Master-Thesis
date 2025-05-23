# modbus_sniffer.py

from scapy.all import sniff, TCP
import threading
import queue
import struct

# Live state and intercepted commands
latest_state = {}
intercepted_commands = queue.Queue()
request_map = {}  # Map transaction ID -> (start_register, quantity, function_code)

# Map register addresses to sensor names
register_to_sensor = {
    1248: "CONSUMERFLOW.DEFECT",
    1024: "CONSUMERFLOW",
    1208: "DEFECT.PUMP1",
    1212: "DEFECT.PUMP2",
    1216: "DEFECT.PUMP3",
    1220: "DEFECT.PUMP4",
    1245: "ENTRYFLOW.DEFECT",
    1018: "ENTRYFLOW",
    1022: "RESERVETANKVOLUME",
    1228: "INPUTVALVE.CLOSE",
    1224: "INPUTVALVE.DEFECT.OPEN",
    1226: "INPUTVALVE.FDC.CLOSE",
    1225: "INPUTVALVE.FDC.OPEN",
    1227: "INPUTVALVE.OPEN",
    1246: "OUTPUTFLOW.DEFECT",
    1020: "OUTPUTFLOW",
    1236: "OUTPUTVALVE.CLOSE",
    1232: "OUTPUTVALVE.DEFECT.OPEN",
    1234: "OUTPUTVALVE.FDC.CLOSE",
    1233: "OUTPUTVALVE.FDC.OPEN",
    1235: "OUTPUTVALVE.OPEN",
    1247: "RESERVETANKVOLUME.DEFECT",
    1404: "STATE.PUMP1",
    1406: "STATE.PUMP2",
    1408: "STATE.PUMP3",
    1410: "STATE.PUMP4",
    1244: "TANKLEVEL.DEFECT",
    1241: "TANKLEVEL.HIGH",
    1240: "TANKLEVEL.LOW",
    1016: "TANKLEVEL"
}

float_registers = [1016, 1018, 1020, 1022, 1024]  # registers to decode as float pairs

# Define the PLC/simulator IP that sends read responses
PLC_IP = "172.17.10.164"  # Update if different

def decode_float_from_registers(low, high):
    combined = (high << 16) | low
    return struct.unpack('>f', combined.to_bytes(4, byteorder='big'))[0]

def is_modbus_packet(pkt):
    return TCP in pkt and (pkt[TCP].dport == 502 or pkt[TCP].sport == 502)

def extract_function_code(pkt):
    payload = bytes(pkt[TCP].payload)
    if len(payload) < 8:
        return None
    return payload[7]

def process_packet(pkt):
    if not is_modbus_packet(pkt):
        return

    try:
        payload = bytes(pkt[TCP].payload)
        fc = extract_function_code(pkt)
        tid = int.from_bytes(payload[0:2], byteorder="big")

        if pkt[0][1].src != PLC_IP:  # request from SCADA (PC2)
            if fc in [0x01, 0x03]:  # Read Coils or Read Holding Registers
                start = int.from_bytes(payload[8:10], byteorder="big")
                count = int.from_bytes(payload[10:12], byteorder="big")
                request_map[tid] = (start, count, fc)

        elif pkt[0][1].src == PLC_IP:  # response from PLC (PC1)
            if tid in request_map:
                start_reg, count, req_fc = request_map.pop(tid)
                byte_count = payload[8]
                values = payload[9:9 + byte_count]

                if req_fc == 0x03:  # Holding Registers
                    i = 0
                    while i < len(values):
                        reg = start_reg + (i // 2)
                        sensor = register_to_sensor.get(reg, f"REG_{reg}")

                        if reg in float_registers and i + 3 < len(values):
                            low = int.from_bytes(values[i:i+2], byteorder='big')
                            high = int.from_bytes(values[i+2:i+4], byteorder='big')
                            value = decode_float_from_registers(low, high)
                            latest_state[sensor] = value
                            print(f"📥 READ (float): {sensor} = {value:.2f}")
                            i += 4
                        else:
                            value = int.from_bytes(values[i:i+2], byteorder='big')
                            latest_state[sensor] = value
                            print(f"📥 READ: {sensor} = {value}")
                            i += 2

                elif req_fc == 0x01:  # Coils (1 bit per register)
                    for i in range(count):
                        byte_index = i // 8
                        bit_index = i % 8
                        if byte_index < len(values):
                            reg = start_reg + i
                            sensor = register_to_sensor.get(reg, f"REG_{reg}")
                            value = (values[byte_index] >> bit_index) & 1
                            latest_state[sensor] = value
                            print(f"📥 READ (Coil): {sensor} = {value}")

                # Assign FLOW.PUMPX as 1/4 of OUTPUTFLOW
                if "OUTPUTFLOW" in latest_state:
                    for x in range(1, 5):
                        latest_state[f"FLOW.PUMP{x}"] = latest_state["OUTPUTFLOW"] / 4

                # Compute CURRENT.FLOW.PUMPX = FLOW × STATE
                for x in range(1, 5):
                    flow_key = f"FLOW.PUMP{x}"
                    state_key = f"STATE.PUMP{x}"
                    current_key = f"CURRENT.FLOW.PUMP{x}"

                    if flow_key in latest_state and state_key in latest_state:
                        latest_state[current_key] = latest_state[flow_key] * latest_state[state_key]

    except Exception as e:
        print(f"⚠️ Error parsing Modbus packet: {e}")

def start_sniffing(interface=None):
    print("📡 Starting Modbus sniffer...")
    sniff(filter="tcp port 502", prn=process_packet, store=0, iface=interface)

def start_sniffing_in_background(interface=None):
    thread = threading.Thread(target=start_sniffing, args=(interface,))
    thread.daemon = True
    thread.start()
