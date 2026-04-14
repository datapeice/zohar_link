# Zohar Link

Optical + TCP demo project for transferring encrypted data.

![Zohar Link Demo](images/image.png)

The repository contains microcontroller artifacts and a Python desktop prototype that:
- sends connection metadata over a laser/UART channel,
- transfers encrypted payload over TCP,
- verifies the laser key on the TCP side via key hash.

## Repository Structure

- `soft_pc/` - Python sender/receiver desktop scripts
- `stm32_files/` - STM32-side files
- `atmega328p_files/` - ATmega328P-side files
- `images/` - project images
- `images/schematic.png` - hardware schematic
- `images/image.png` - project preview

## Requirements

- Python 3.10+
- Serial ports configured and connected (sender and receiver)
- Python packages:

```bash
pip install pyserial pycryptodome
```

## Configuration

Edit these values if needed:

- `soft_pc/sender.py`
  - `SERIAL_PORT` (default `COM6`)
  - `MY_IP` (default `127.0.0.1`)
  - `PORT` (default `65432`)
- `soft_pc/receiver.py`
  - `SERIAL_PORT` (default `COM5`)

For local testing on one machine, keep `MY_IP=127.0.0.1`.

## Run

Open two terminals in the repository root.

1) Start receiver:

```bash
python soft_pc/receiver.py
```

2) Start sender:

```bash
python soft_pc/sender.py
```

## Current Data Flow

1. Sender generates AES-256 key.
2. Sender sends laser packet over UART:

`IP:PORT:AES_KEY_B64:FILE_SHA256*`

3. Sender prepares encrypted payload and starts TCP server.
4. Receiver parses laser packet, connects to sender TCP server, receives payload.
5. Receiver verifies key hash from TCP against laser key and decrypts message.

## Physical Layer Notes

- Laser transmission currently uses Manchester encoding.
- Current practical transmission speed is 100 baud.
- The project is still under active development, and the physical/link layer is planned for further optimization and reliability improvements.

## Important Runtime Notes

- If receiver shows `Packet parse error`, UART packet was corrupted.
  - Receiver asks: `Press y to continue listening:`
  - Press `y` to keep waiting for the next packet.
- If receiver shows `WinError 10061`, sender TCP server was not ready or closed.
  - Start receiver first, then sender.
  - Do not interrupt sender before it reaches TCP listening state.
- `Ctrl+C` is handled gracefully in both scripts.

## Security Note

This is a prototype/demo implementation for lab usage. For production use, add:
- robust packet framing + CRC on UART,
- retries/acknowledgements,
- authenticated protocol versioning,
- stronger error recovery logic.
