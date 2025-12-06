"""
Real-time MIDI to LED synchronization.

Synchronizes MIDI drum input (e.g., from GarageBand) with LED light control,
creating visual responses to drum hits in real-time.
"""

import asyncio
import sys
import argparse
import logging
from typing import Optional, Tuple
from asyncio import Queue

from led.midi_handler import MIDIHandler
from led.drum_mapper import DrumMapper, DrumType
from led.neon import LEDController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MIDISync:
    """Main orchestrator for MIDI-to-LED synchronization."""

    def __init__(
        self,
        midi_port: Optional[str] = None,
        led_address: Optional[str] = None,
        flash_duration: float = 0.1,
    ):
        """
        Initialize MIDI sync.
        
        Args:
            midi_port: MIDI input port name. If None, will auto-detect.
            led_address: LED device address. If None, will prompt for selection.
            flash_duration: Duration in seconds for flash effect on drum hit.
        """
        self.midi_handler = MIDIHandler()
        self.drum_mapper = DrumMapper()
        self.led_controller = LEDController()
        self.midi_port = midi_port
        self.led_address = led_address
        self.flash_duration = flash_duration
        self.midi_queue: Queue[Tuple[int, int]] = Queue()
        self.running = False
        self.original_brightness: Optional[int] = None
        self.original_color: Optional[Tuple[int, int, int]] = None

    async def setup_midi(self) -> bool:
        """Set up MIDI input connection."""
        ports = self.midi_handler.list_input_ports()
        
        if not ports:
            print("❌ No MIDI input ports found!")
            print("   Make sure GarageBand is running and configured to send MIDI.")
            return False

        print("\n📻 Available MIDI input ports:")
        for i, port in enumerate(ports, 1):
            marker = " ← GarageBand" if "garageband" in port.lower() or "iac" in port.lower() else ""
            print(f"   {i}. {port}{marker}")

        # Auto-select or prompt
        if self.midi_port:
            if self.midi_port not in ports:
                print(f"❌ Port '{self.midi_port}' not found!")
                return False
            selected_port = self.midi_port
        else:
            # Auto-detect GarageBand
            selected_port = None
            for port in ports:
                if "garageband" in port.lower() or "iac" in port.lower():
                    selected_port = port
                    break
            
            if not selected_port:
                if len(ports) == 1:
                    selected_port = ports[0]
                else:
                    try:
                        choice = input(f"\nSelect MIDI port (1-{len(ports)}) or press Enter for first: ").strip()
                        if choice:
                            idx = int(choice) - 1
                            if 0 <= idx < len(ports):
                                selected_port = ports[idx]
                            else:
                                print("Invalid selection")
                                return False
                        else:
                            selected_port = ports[0]
                    except (ValueError, KeyboardInterrupt):
                        return False

        if self.midi_handler.connect(selected_port):
            print(f"✅ Connected to MIDI port: {selected_port}")
            # Set callback to queue MIDI events
            self.midi_handler.set_callback(self._midi_callback)
            return True
        return False

    def _midi_callback(self, note: int, velocity: int):
        """Callback for MIDI events (runs in MIDI thread)."""
        # Put event in queue for async processing
        try:
            self.midi_queue.put_nowait((note, velocity))
        except Exception as e:
            logger.error(f"Error queueing MIDI event: {e}")

    async def setup_led(self) -> bool:
        """Set up LED device connection."""
        print("\n💡 Scanning for LEDDMX devices...")
        devices = await self.led_controller.scan_devices()

        if not devices:
            print("❌ No LEDDMX devices found!")
            return False

        print(f"\n💡 Found {len(devices)} LEDDMX device(s):")
        for i, (address, name) in enumerate(devices, 1):
            print(f"   {i}. {name} - {address}")

        # Auto-select or prompt
        if self.led_address:
            if not any(addr == self.led_address for addr, _ in devices):
                print(f"❌ Device '{self.led_address}' not found!")
                return False
            selected_address = self.led_address
        else:
            if len(devices) == 1:
                selected_address = devices[0][0]
            else:
                try:
                    choice = input(f"\nSelect LED device (1-{len(devices)}) or press Enter for first: ").strip()
                    if choice:
                        idx = int(choice) - 1
                        if 0 <= idx < len(devices):
                            selected_address = devices[idx][0]
                        else:
                            print("Invalid selection")
                            return False
                    else:
                        selected_address = devices[0][0]
                except (ValueError, KeyboardInterrupt):
                    return False

        print(f"\n🔌 Connecting to LED device...")
        if await self.led_controller.connect(selected_address):
            print(f"✅ Connected to LED device: {selected_address}")
            # Turn on and set initial state
            await self.led_controller.power(True)
            # Store original settings for restoration
            self.original_brightness = 50  # Default
            self.original_color = (255, 255, 255)  # White
            await self.led_controller.set_brightness(self.original_brightness)
            await self.led_controller.set_color(*self.original_color)
            return True
        return False

    async def process_midi_event(self, note: int, velocity: int):
        """
        Process a MIDI event and trigger LED response.
        
        Args:
            note: MIDI note number
            velocity: MIDI velocity (0-127)
        """
        # Get drum type, color, and brightness
        drum_type = self.drum_mapper.get_drum_type(note)
        color, brightness = self.drum_mapper.get_color_and_brightness(note, velocity)
        drum_name = self.drum_mapper.get_drum_name(note)

        logger.debug(f"Drum hit: {drum_name} (note {note}, velocity {velocity}) -> RGB{color} @ {brightness}%")

        # Flash effect: set color and brightness, then fade back
        try:
            # Set color and brightness for the hit
            await self.led_controller.set_color(*color)
            await self.led_controller.set_brightness(brightness)
            
            # Wait for flash duration
            await asyncio.sleep(self.flash_duration)
            
            # Fade back to original (or dimmed version)
            fade_brightness = max(20, int(brightness * 0.3))  # Fade to 30% of hit brightness, min 20%
            await self.led_controller.set_brightness(fade_brightness)
            
        except Exception as e:
            logger.error(f"Error processing MIDI event: {e}")

    async def run(self):
        """Main run loop - processes MIDI events and controls LEDs."""
        # Setup MIDI
        if not await self.setup_midi():
            return False

        # Setup LED
        if not await self.setup_led():
            self.midi_handler.disconnect()
            return False

        # Start listening for MIDI events
        self.midi_handler.start_listening()
        self.running = True

        print("\n" + "="*60)
        print("🎵 MIDI-to-LED Sync Active!")
        print("="*60)
        print("Hit your drums in GarageBand to see the lights respond!")
        print("Press Ctrl+C to stop.")
        print("="*60 + "\n")

        try:
            # Main event loop
            while self.running:
                try:
                    # Wait for MIDI event with timeout to allow checking running state
                    note, velocity = await asyncio.wait_for(
                        self.midi_queue.get(), timeout=0.5
                    )
                    # Process the event
                    await self.process_midi_event(note, velocity)
                except asyncio.TimeoutError:
                    # Timeout is fine, just check if we should continue
                    continue
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping...")
        finally:
            await self.cleanup()

        return True

    async def cleanup(self):
        """Clean up resources."""
        self.running = False
        self.midi_handler.stop_listening()
        self.midi_handler.disconnect()
        
        # Restore LED to original state
        if self.led_controller.client and self.led_controller.client.is_connected:
            try:
                if self.original_brightness is not None:
                    await self.led_controller.set_brightness(self.original_brightness)
                if self.original_color:
                    await self.led_controller.set_color(*self.original_color)
            except Exception as e:
                logger.error(f"Error restoring LED state: {e}")
        
        await self.led_controller.disconnect()
        print("✅ Cleaned up and disconnected")


class Args(argparse.Namespace):
    """Command-line arguments."""
    midi_port: Optional[str]
    led_address: Optional[str]
    flash_duration: float
    verbose: bool


async def main(args: Args):
    """Main entry point."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sync = MIDISync(
        midi_port=args.midi_port,
        led_address=args.led_address,
        flash_duration=args.flash_duration,
    )

    success = await sync.run()
    return 0 if success else 1


def cli():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Sync real-time MIDI drum input (e.g., GarageBand) with LED lights"
    )

    parser.add_argument(
        "--midi-port",
        type=str,
        help="MIDI input port name (auto-detects GarageBand if not specified)",
    )

    parser.add_argument(
        "--led-address",
        type=str,
        help="LED device Bluetooth address (prompts for selection if not specified)",
    )

    parser.add_argument(
        "--flash-duration",
        type=float,
        default=0.1,
        help="Duration in seconds for flash effect on drum hit (default: 0.1)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args(namespace=Args())

    try:
        exit_code = asyncio.run(main(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

