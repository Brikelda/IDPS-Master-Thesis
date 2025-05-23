from scapy.all import sniff, TCP

def is_modbus_packet(pkt):
    return TCP in pkt and (pkt[TCP].dport == 502 or pkt[TCP].sport == 502)

def print_packet_info(pkt):
    if not is_modbus_packet(pkt):
        return

    try:
        payload = bytes(pkt[TCP].payload)
        fc = payload[7] if len(payload) >= 8 else None

        print("\n📦 Packet received:")
        print(f"    Source IP:   {pkt[0][1].src}")
        print(f"    Destination: {pkt[0][1].dst}")
        print(f"    Function code: {fc}")
        print(f"    Raw payload: {payload.hex()}")
    except Exception as e:
        print(f"⚠️ Error reading packet: {e}")

print("📡 Starting Modbus sniffer on port 502...")
sniff(filter="tcp port 502", prn=print_packet_info, store=0, iface="Ethernet")  # Replace iface with your interface name
