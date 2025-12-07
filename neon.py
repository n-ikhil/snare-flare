"""
LED Control Script for LEDDMX-00/03 Bluetooth LED devices

This script discovers LEDDMX devices, allows device selection,
and provides interactive control using the LEDDMX-00 protocol.

Based on: https://github.com/user154lt/LEDDMX-00
"""

import asyncio
import sys
from typing import List, Tuple, Optional
from bleak import BleakScanner, BleakClient
import struct

# LEDDMX-00 BLE UUIDs
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Pattern names (from PatternList.kt)
PATTERNS = [
    "Off",
    "Forward Dreaming", "Backward Dreaming",
    "Forward 7 Colors", "Backward 7 Colors",
    "Forward RD/GN/BU", "Backward RD/GN/BU",
    "Forward YE/CN/VT", "Backward YE/CN/VT",
    # ... (truncated for brevity, we'll include key ones)
    "Strobe 7 Colors", "Strobe RD/GN/BU", "Strobe YE/CN/VT",
]

class LEDController:
    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None

    async def scan_devices(self) -> List[Tuple[str, str]]:
        """Scan for LEDDMX devices and return list of (address, name) tuples."""
        print("Scanning for LEDDMX devices... (5 seconds)")
        devices = await BleakScanner.discover(return_adv=True)

        leddmx_devices = []
        for device, adv in devices.values():
            if device.name and device.name.startswith("LEDDMX"):
                leddmx_devices.append((device.address, device.name))

        return leddmx_devices

    async def connect(self, address: str) -> bool:
        """Connect to the specified BLE device."""
        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.device_address = address
            print(f"Connected to {address}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the current device."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected")
        self.client = None
        self.device_address = None

    async def send_command(self, command_bytes: bytes):
        """Send a command to the LED device."""
        if not self.client or not self.client.is_connected:
            print("Not connected to device")
            return False

        try:
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, command_bytes)
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False

    # Control commands based on LEDDMX-00 protocol

    async def power(self, on: bool):
        """Turn lights on or off."""
        power_byte = 0x03 if on else 0x02
        command = bytes([0x7B, 0xFF, 0x04, power_byte, 0xFF, 0xFF, 0xFF, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            print(f"Power {'ON' if on else 'OFF'}")

    async def set_color(self, r: int, g: int, b: int):
        """Set RGB color."""
        command = bytes([0x7B, 0xFF, 0x07, r, g, b, 0x00, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            print(f"Set color to RGB({r}, {g}, {b})")

    async def set_brightness(self, brightness: int):
        """Set brightness (0-100)."""
        brightness = max(0, min(100, brightness))
        adjusted = (brightness * 32) // 100
        command = bytes([0x7B, 0xFF, 0x01, adjusted, brightness, 0x00, 0xFF, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            print(f"Set brightness to {brightness}%")

    async def set_pattern(self, pattern_index: int):
        """Set pattern by index (0-210)."""
        pattern_index = max(0, min(210, pattern_index))
        command = bytes([0x7B, 0xFF, 0x03, pattern_index, 0xFF, 0xFF, 0xFF, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            pattern_name = PATTERNS[pattern_index] if pattern_index < len(PATTERNS) else f"Pattern {pattern_index}"
            print(f"Set pattern: {pattern_name}")

    async def set_color_temperature(self, temperature: int):
        """Set color temperature (0-100)."""
        temperature = max(0, min(100, temperature))
        adjusted = (temperature * 32) // 100
        command = bytes([0x7B, 0xFF, 0x09, adjusted, temperature, 0xFF, 0xFF, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            print(f"Set color temperature to {temperature}%")

    async def set_mic_eq(self, eq_mode: int):
        """Set microphone EQ mode (0=off, 1-255=on with different effects)."""
        eq_mode = max(0, min(255, eq_mode))
        command = bytes([0x7B, 0xFF, 0x0B, eq_mode, 0x00, 0xFF, 0xFF, 0xBF])
        success = await self.send_command(command)
        if success:
            if eq_mode == 0:
                print("Microphone OFF")
            else:
                print(f"Microphone EQ mode: {eq_mode}")

    def get_preset_colors(self):
        """Get common preset colors."""
        return {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "white": (255, 255, 255),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128),
            "pink": (255, 192, 203),
        }


async def main():
    controller = LEDController()

    try:
        # Step 1: Scan for devices
        devices = await controller.scan_devices()

        if not devices:
            print("No LEDDMX devices found!")
            return

        print(f"\nFound {len(devices)} LEDDMX device(s):")
        for i, (address, name) in enumerate(devices, 1):
            print(f"{i}. {name} - {address}")

        # Step 2: Device selection
        while True:
            try:
                choice = input("\nEnter device number to connect (or 'q' to quit): ").strip()
                if choice.lower() == 'q':
                    return

                device_index = int(choice) - 1
                if 0 <= device_index < len(devices):
                    selected_address, selected_name = devices[device_index]
                    break
                else:
                    print("Invalid choice. Please select a valid device number.")
            except ValueError:
                print("Please enter a number or 'q' to quit.")

        # Step 3: Connect to device
        print(f"\nConnecting to {selected_name}...")
        if not await controller.connect(selected_address):
            return

        # Step 4: Interactive control menu
        preset_colors = controller.get_preset_colors()

        while True:
            print("\n" + "="*50)
            print("LED Control Menu:")
            print("="*50)
            print("1. Power ON")
            print("2. Power OFF")
            print("3. Set RGB Color")
            print("4. Set Preset Color")
            print("5. Set Brightness")
            print("6. Set Pattern")
            print("7. Set Color Temperature")
            print("8. Microphone/EQ Control")
            print("9. Disconnect and quit")
            print("="*50)

            choice = input("Enter your choice (1-9): ").strip()

            try:
                if choice == "1":
                    await controller.power(True)

                elif choice == "2":
                    await controller.power(False)

                elif choice == "3":
                    r = int(input("Red (0-255): "))
                    g = int(input("Green (0-255): "))
                    b = int(input("Blue (0-255): "))
                    await controller.set_color(r, g, b)

                elif choice == "4":
                    print("\nPreset colors:")
                    for name, rgb in preset_colors.items():
                        print(f"  {name}: RGB{rgb}")
                    color_name = input("Enter color name: ").strip().lower()
                    if color_name in preset_colors:
                        r, g, b = preset_colors[color_name]
                        await controller.set_color(r, g, b)
                    else:
                        print("Color not found.")

                elif choice == "5":
                    brightness = int(input("Brightness (0-100): "))
                    await controller.set_brightness(brightness)

                elif choice == "6":
                    print(f"\nAvailable patterns (0-{len(PATTERNS)-1}):")
                    for i, pattern in enumerate(PATTERNS[:20]):  # Show first 20
                        print(f"  {i}: {pattern}")
                    if len(PATTERNS) > 20:
                        print(f"  ... and {len(PATTERNS)-20} more patterns")
                    pattern_idx = int(input("Enter pattern number: "))
                    await controller.set_pattern(pattern_idx)

                elif choice == "7":
                    temp = int(input("Color temperature (0-100): "))
                    await controller.set_color_temperature(temp)

                elif choice == "8":
                    eq_mode = int(input("EQ mode (0=off, 1-255=on with effects): "))
                    await controller.set_mic_eq(eq_mode)

                elif choice == "9":
                    break

                else:
                    print("Invalid choice. Please select 1-9.")

            except ValueError as e:
                print(f"Invalid input: {e}")
            except KeyboardInterrupt:
                break

    finally:
        await controller.disconnect()


def cli():
    """Command-line entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    cli()
