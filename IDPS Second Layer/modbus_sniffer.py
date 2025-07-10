# modbus_sniffer.py for Second Layer (WRITE interception)

from scapy.all import sniff, TCP
import threading
import queue

# Live intercepted write commands
intercepted_commands = queue.Queue()
request_map = {}

# Define IPs
SCADA_IP = "172.17.10.165"  # PC2
PLC_IP = "172.17.10.164"    # PC1

# Map register addresses to sensor names
register_to_sensor = {
    478: "DEFECT.PUMP1",
    479: "DEFECT.PUMP2",
    480: "DEFECT.PUMP3",
    481: "DEFECT.PUMP4",
    482: "STATE.PUMP1",
    483: "STATE.PUMP2",
    484: "STATE.PUMP3",
    485: "STATE.PUMP4",
    102: "OUTPUTFLOW"
}

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

        if pkt[0][1].src == SCADA_IP and pkt[0][1].dst == PLC_IP:
            # Handle WRITE commands
            if fc == 0x06:  # Write Single Register
                register = int.from_bytes(payload[8:10], byteorder='big')
                value = int.from_bytes(payload[10:12], byteorder='big')
                sensor = register_to_sensor.get(register, f"REG_{register}")
                print(f"✏️ WRITE: {sensor} = {value}")
                intercepted_commands.put({sensor: value})

            elif fc == 0x10:  # Write Multiple Registers
                start = int.from_bytes(payload[8:10], byteorder='big')
                count = int.from_bytes(payload[10:12], byteorder='big')
                byte_count = payload[12]
                data = payload[13:13 + byte_count]

                for i in range(0, byte_count, 2):
                    reg = start + (i // 2)
                    value = int.from_bytes(data[i:i+2], byteorder='big')
                    sensor = register_to_sensor.get(reg, f"REG_{reg}")
                    print(f"✏️ WRITE (multi): {sensor} = {value}")
                    intercepted_commands.put({sensor: value})

    except Exception as e:
        print(f"⚠️ Error processing write packet: {e}")

def start_sniffing(interface=None):
    print("📡 Starting WRITE sniffer for Second Layer...")
    sniff(filter="tcp port 502", prn=process_packet, store=0, iface=interface)

def start_sniffing_in_background(interface=None):
    thread = threading.Thread(target=start_sniffing, args=(interface,))
    thread.daemon = True
    thread.start()
