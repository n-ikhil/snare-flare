"""
Drum Mapper - Maps MIDI note numbers to drum types and visual effects.

Provides standard General MIDI (GM) drum kit mappings and configurable
color/effect assignments per drum type.
"""

from typing import Dict, Tuple, Optional
from enum import Enum


class DrumType(str, Enum):
    """Drum types for categorization."""
    KICK = "kick"
    SNARE = "snare"
    HIHAT = "hihat"
    CRASH = "crash"
    RIDE = "ride"
    TOM = "tom"
    UNKNOWN = "unknown"


# Standard General MIDI (GM) Drum Kit Note Mappings
DRUM_NOTES: Dict[int, DrumType] = {
    # Kick drums
    36: DrumType.KICK,  # Acoustic Bass Drum
    35: DrumType.KICK,  # Electric Bass Drum
    
    # Snare drums
    38: DrumType.SNARE,  # Acoustic Snare
    40: DrumType.SNARE,  # Electric Snare
    
    # Hi-Hats
    42: DrumType.HIHAT,  # Closed Hi-Hat
    44: DrumType.HIHAT,  # Pedal Hi-Hat
    46: DrumType.HIHAT,  # Open Hi-Hat
    
    # Crash cymbals
    49: DrumType.CRASH,  # Crash Cymbal 1
    57: DrumType.CRASH,  # Crash Cymbal 2
    
    # Ride cymbals
    51: DrumType.RIDE,  # Ride Cymbal 1
    59: DrumType.RIDE,  # Ride Cymbal 2
    
    # Toms
    41: DrumType.TOM,  # Low Floor Tom
    43: DrumType.TOM,  # High Floor Tom
    45: DrumType.TOM,  # Low Tom
    47: DrumType.TOM,  # Low-Mid Tom
    48: DrumType.TOM,  # Hi-Mid Tom
    50: DrumType.TOM,  # High Tom
}

# Default color mappings (RGB 0-255)
DEFAULT_DRUM_COLORS: Dict[DrumType, Tuple[int, int, int]] = {
    DrumType.KICK: (255, 0, 0),      # Red
    DrumType.SNARE: (255, 255, 255), # White
    DrumType.HIHAT: (0, 255, 255),   # Cyan
    DrumType.CRASH: (255, 255, 0),   # Yellow
    DrumType.RIDE: (255, 165, 0),    # Orange
    DrumType.TOM: (0, 255, 0),        # Green
    DrumType.UNKNOWN: (128, 128, 128), # Gray
}


class DrumMapper:
    """Maps MIDI notes to drum types and provides color/effect mappings."""

    def __init__(
        self,
        drum_colors: Optional[Dict[DrumType, Tuple[int, int, int]]] = None,
        velocity_to_brightness: bool = True,
    ):
        """
        Initialize drum mapper.
        
        Args:
            drum_colors: Custom color mapping. If None, uses defaults.
            velocity_to_brightness: If True, map MIDI velocity to brightness.
        """
        self.drum_colors = drum_colors or DEFAULT_DRUM_COLORS.copy()
        self.velocity_to_brightness = velocity_to_brightness

    def get_drum_type(self, note: int) -> DrumType:
        """
        Get drum type for a MIDI note number.
        
        Args:
            note: MIDI note number (0-127)
        
        Returns:
            DrumType enum value
        """
        return DRUM_NOTES.get(note, DrumType.UNKNOWN)

    def get_color(self, note: int) -> Tuple[int, int, int]:
        """
        Get RGB color for a MIDI note.
        
        Args:
            note: MIDI note number (0-127)
        
        Returns:
            RGB tuple (r, g, b) with values 0-255
        """
        drum_type = self.get_drum_type(note)
        return self.drum_colors.get(drum_type, DEFAULT_DRUM_COLORS[DrumType.UNKNOWN])

    def get_brightness(self, velocity: int) -> int:
        """
        Map MIDI velocity to brightness percentage.
        
        Args:
            velocity: MIDI velocity (0-127)
        
        Returns:
            Brightness percentage (0-100)
        """
        if not self.velocity_to_brightness:
            return 100
        
        # Map velocity (0-127) to brightness (0-100)
        # Minimum brightness of 30% for visibility, max 100%
        min_brightness = 30
        max_brightness = 100
        brightness = min_brightness + int((velocity / 127) * (max_brightness - min_brightness))
        return brightness

    def get_color_and_brightness(
        self, note: int, velocity: int
    ) -> Tuple[Tuple[int, int, int], int]:
        """
        Get both color and brightness for a MIDI note and velocity.
        
        Args:
            note: MIDI note number (0-127)
            velocity: MIDI velocity (0-127)
        
        Returns:
            Tuple of (RGB color tuple, brightness percentage)
        """
        color = self.get_color(note)
        brightness = self.get_brightness(velocity)
        return color, brightness

    def set_drum_color(self, drum_type: DrumType, color: Tuple[int, int, int]):
        """
        Set custom color for a drum type.
        
        Args:
            drum_type: DrumType enum value
            color: RGB tuple (r, g, b) with values 0-255
        """
        self.drum_colors[drum_type] = color

    def get_drum_name(self, note: int) -> str:
        """
        Get human-readable drum name for a MIDI note.
        
        Args:
            note: MIDI note number (0-127)
        
        Returns:
            String name of the drum
        """
        drum_type = self.get_drum_type(note)
        return drum_type.value

