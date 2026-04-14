import socket
import serial
import base64
import hashlib
import struct
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import time

SERIAL_PORT = 'COM6'
BAUD_RATE = 115200
HOST = '0.0.0.0'
MY_IP = '127.0.0.1'
PORT = 65432

SECRET_MESSAGE = b"Shalom aleichem, this is a secret message"

def main():
    print("Sohar link - sender node")
    print("Developed by @datapeice")

    print("[1] Generating 256-bit AES key...")
    aes_key = get_random_bytes(32)
    aes_key_b64 = base64.b64encode(aes_key).decode('utf-8')
    laser_file_checksum = hashlib.sha256(SECRET_MESSAGE).hexdigest()

    laser_msg = f"{MY_IP}:{PORT}:{aes_key_b64}:{laser_file_checksum}*\n".encode('utf-8')

    print(f"[2] Packet size: {len(laser_msg)} bytes. Opening {SERIAL_PORT}...")

    with serial.Serial(SERIAL_PORT, BAUD_RATE) as ser:
        time.sleep(2)
        print("sending packet")
        for byte in laser_msg:
            ser.write(bytes([byte]))
            ser.flush()
            time.sleep(0.12)

    print("[3] Encrypting payload before TCP transfer...")
    cipher_aes = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(SECRET_MESSAGE)
    encrypted_payload = cipher_aes.nonce + tag + ciphertext
    key_hash_tcp = hashlib.sha256(aes_key).digest()
    framed_payload = struct.pack("!I", len(encrypted_payload)) + encrypted_payload + key_hash_tcp

    print(f"\n[4] Starting TCP server on port {PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0)
        print("Waiting for receiver connection...")

        while True:
            try:
                conn, addr = s.accept()
                break
            except socket.timeout:
                continue

        with conn:
            print(f"Receiver connected: {addr}")

            print("[5] Sending pre-encrypted payload via TCP...")
            conn.sendall(framed_payload)
            print("TCP payload sent successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Sender stopped.")
    except Exception as e:
        print(f"Sender error: {e}")
