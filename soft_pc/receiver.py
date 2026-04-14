import socket
import serial
import base64
import hashlib
import struct
from Crypto.Cipher import AES

SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Socket closed before receiving expected bytes.")
        data.extend(chunk)
    return bytes(data)

def read_laser_packet_live(ser):
    packet = bytearray()
    started = False
    while True:
        byte = ser.read(1)
        if byte:
            started = True
            if byte == b'\n' or byte == b'*':
                break
            packet.extend(byte)
            print(byte.decode('utf-8', errors='ignore'), end='', flush=True)
        elif started:
            break
    return bytes(packet).strip()

def parse_laser_packet(packet_bytes):
    packet_text = packet_bytes.decode('utf-8')
    parts = packet_text.split(':')
    if len(parts) != 4:
        raise ValueError("Invalid packet shape.")

    server_ip = parts[0]
    server_port = int(parts[1])
    aes_key_b64 = parts[2]
    laser_file_checksum = parts[3]

    socket.inet_aton(server_ip)
    if server_port < 1 or server_port > 65535:
        raise ValueError("Invalid TCP port.")

    aes_key = base64.b64decode(aes_key_b64, validate=True)
    if len(aes_key) != 32:
        raise ValueError("Invalid AES-256 key length.")

    return server_ip, server_port, aes_key, laser_file_checksum

def main():
    print("Sohar link - receiver node")
    print("Developed by @datapeice")
    print(f"\n[1] Listening for laser packet on {SERIAL_PORT}...")

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5) as ser:
        print("Receiving laser data: ", end='', flush=True)
        server_ip = None
        server_port = None
        aes_key = None
        laser_file_checksum = None

        while True:
            raw_data = read_laser_packet_live(ser)
            if not raw_data:
                continue

            print("\n\nPacket received.")
            try:
                server_ip, server_port, aes_key, laser_file_checksum = parse_laser_packet(raw_data)
                print("Packet parsed.")
                break
            except Exception as parse_error:
                print(f"Packet parse error: {parse_error}")
                user_choice = input("Press y to continue listening: ").strip().lower()
                if user_choice != "y":
                    print("Receiver stopped by user.")
                    return
                print("Waiting for next packet...")
                print("Receiving laser data: ", end='', flush=True)

        try:
            print(f"Sender IP: {server_ip}")
            print(f"Sender TCP port: {server_port}")

            print("Laser key decoded.")

            print(f"\n[2] Connecting to TCP sender {server_ip}:{server_port}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_ip, server_port))

                payload_length = struct.unpack("!I", recv_exact(s, 4))[0]
                if payload_length < 32:
                    raise ValueError("Invalid TCP payload length.")
                encrypted_payload = recv_exact(s, payload_length)
                received_key_hash = recv_exact(s, 32)
                expected_key_hash = hashlib.sha256(aes_key).digest()

                if received_key_hash != expected_key_hash:
                    raise ValueError("Key hash verification failed.")

                print(f"Encrypted payload received: {len(encrypted_payload)} bytes.")
                nonce = encrypted_payload[:16]
                tag = encrypted_payload[16:32]
                ciphertext = encrypted_payload[32:]

                cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
                decrypted_msg = cipher_aes.decrypt_and_verify(ciphertext, tag)

                print(f"Laser file hash: {laser_file_checksum}")

                print("\n" + "="*50)
                print("Decrypted payload:")
                print(decrypted_msg.decode('utf-8'))
                print("="*50)

        except Exception as e:
            print(f"Processing error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Receiver stopped.")
    except Exception as e:
        print(f"Receiver error: {e}")
