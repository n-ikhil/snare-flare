"""
MIDI Input Handler for real-time MIDI event processing.

Handles MIDI port discovery, connection, and real-time message callbacks.
"""

import mido
from typing import List, Optional, Callable
import threading
import logging

logger = logging.getLogger(__name__)


class MIDIHandler:
    """Handles MIDI input from external sources (e.g., GarageBand)."""

    def __init__(self, verbose: bool = False):
        self.port: Optional[mido.ports.BaseInput] = None
        self.port_name: Optional[str] = None
        self.callback: Optional[Callable[[int, int], None]] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.verbose = verbose

    def list_input_ports(self) -> List[str]:
        """List all available MIDI input ports."""
        return mido.get_input_names()

    def connect(self, port_name: Optional[str] = None) -> bool:
        """
        Connect to a MIDI input port.
        
        Args:
            port_name: Name of the port to connect to. If None, auto-detects
                      GarageBand or uses first available port.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            available_ports = self.list_input_ports()
            
            if not available_ports:
                logger.error("No MIDI input ports available")
                return False

            # Auto-detect GarageBand if no port specified
            if port_name is None:
                for port in available_ports:
                    if "garageband" in port.lower() or "iac" in port.lower():
                        port_name = port
                        break
                
                # Fallback to first available port
                if port_name is None:
                    port_name = available_ports[0]

            if port_name not in available_ports:
                logger.error(f"Port '{port_name}' not found. Available ports: {available_ports}")
                return False

            self.port = mido.open_input(port_name)
            self.port_name = port_name
            logger.info(f"Connected to MIDI port: {port_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MIDI port: {e}")
            return False

    def disconnect(self):
        """Disconnect from the current MIDI port."""
        self.stop_listening()
        if self.port:
            try:
                self.port.close()
            except Exception as e:
                logger.error(f"Error closing MIDI port: {e}")
            self.port = None
            self.port_name = None

    def set_callback(self, callback: Callable[[int, int], None]):
        """
        Set callback function for MIDI Note On events.
        
        Args:
            callback: Function that takes (note: int, velocity: int) as arguments.
                     Called when a Note On event is received.
        """
        self.callback = callback

    def _process_midi_message(self, msg: mido.Message):
        """Process a MIDI message and trigger callback if it's a Note On event."""
        # Log all MIDI messages for debugging
        if self.verbose:
            logger.info(f"MIDI message: {msg}")
        else:
            logger.debug(f"MIDI message received: {msg}")
        
        if msg.type == 'note_on' and msg.velocity > 0:
            # Note On event with velocity > 0 (actual hit)
            logger.info(f"🎵 Drum hit detected: note={msg.note}, velocity={msg.velocity}")
            if self.callback:
                try:
                    self.callback(msg.note, msg.velocity)
                except Exception as e:
                    logger.error(f"Error in MIDI callback: {e}")
        elif msg.type == 'note_on' and msg.velocity == 0:
            # Note On with velocity 0 is actually a Note Off
            if self.verbose:
                logger.info(f"Note Off (via note_on): note={msg.note}")
            else:
                logger.debug(f"Note Off: note={msg.note}")
        elif msg.type == 'note_off':
            if self.verbose:
                logger.info(f"Note Off: note={msg.note}")
            else:
                logger.debug(f"Note Off: note={msg.note}")

    def _listen_loop(self):
        """Internal loop that listens for MIDI messages."""
        if not self.port:
            return

        try:
            for msg in self.port:
                if not self.running:
                    break
                self._process_midi_message(msg)
        except Exception as e:
            if self.running:  # Only log if we're supposed to be running
                logger.error(f"Error in MIDI listen loop: {e}")

    def start_listening(self):
        """Start listening for MIDI events in a background thread."""
        if self.running:
            return

        if not self.port:
            logger.error("Cannot start listening: not connected to a MIDI port")
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info("Started listening for MIDI events")

    def stop_listening(self):
        """Stop listening for MIDI events."""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.info("Stopped listening for MIDI events")

    def is_connected(self) -> bool:
        """Check if connected to a MIDI port."""
        return self.port is not None and not self.port.closed

