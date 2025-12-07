# Real-Time GarageBand Drum MIDI to LED Control - Implementation Plan

## Overview
This plan outlines how to synchronize real-time MIDI drum input from GarageBand with LED light control, creating visual responses to drum hits.

## Architecture

```
GarageBand (MIDI Output)
    ↓
MIDI Input Handler (Python)
    ↓
Drum Hit Detector & Mapper
    ↓
LED Controller (BLE)
    ↓
LEDDMX Device
```

## Components Required

### 1. MIDI Input Library
- **mido** - High-level MIDI library (recommended for ease of use)
- **python-rtmidi** - Lower-level, better performance (alternative)
- On macOS, both can use CoreMIDI backend

### 2. Existing Components (Already Available)
- `LEDController` class in `led/neon.py` - Handles BLE communication
- BLE device discovery and connection
- Color, brightness, pattern control

### 3. New Components Needed

#### a. MIDI Input Handler (`led/midi_handler.py`)
- List available MIDI input ports
- Connect to GarageBand's virtual MIDI port
- Receive MIDI messages in real-time
- Filter for Note On/Off events (drum hits)

#### b. Drum Mapper (`led/drum_mapper.py`)
- Map MIDI note numbers to drum types:
  - Kick (36, 35)
  - Snare (38, 40)
  - Hi-Hat (42, 44, 46)
  - Crash (49, 57)
  - Ride (51, 59)
  - Toms (41, 43, 45, 47, 48)
- Map velocity to brightness/intensity
- Optional: Map different drums to different colors

#### c. MIDI-to-LED Sync (`led/midi_sync.py`)
- Main orchestrator that:
  - Initializes MIDI input
  - Connects to LED device
  - Processes MIDI events → triggers LED effects
  - Handles real-time timing

## Implementation Steps

### Phase 1: Dependencies & Setup
1. Add MIDI library to `pyproject.toml`:
   - `mido>=1.2.10` (or `python-rtmidi>=1.4.9`)
   - If using mido, may need `python-rtmidi` as backend

2. Install dependencies:
   ```bash
   uv sync
   ```

### Phase 2: MIDI Input Handler
1. Create `led/midi_handler.py`:
   - List MIDI input ports
   - Connect to selected port (or auto-detect GarageBand)
   - Callback-based MIDI message handling
   - Filter Note On events (velocity > 0)
   - Extract note number and velocity

### Phase 3: Drum Mapping
1. Create `led/drum_mapper.py`:
   - Standard MIDI drum note mappings
   - Configurable color per drum type
   - Velocity-to-brightness mapping
   - Optional: Different effects per drum (flash, strobe, color change)

### Phase 4: Real-Time Sync
1. Create `led/midi_sync.py`:
   - Async/await architecture (compatible with existing LEDController)
   - MIDI callback → async LED control
   - Queue system for MIDI events (if needed)
   - Error handling and reconnection logic

### Phase 5: CLI Integration
1. Create command-line interface:
   - List MIDI ports
   - Select MIDI input port
   - Connect to LED device
   - Start real-time sync
   - Optional: Configuration file for drum mappings

## Technical Considerations

### Real-Time Performance
- **Latency**: Target <50ms from MIDI event to LED response
- **Threading**: MIDI callbacks run in separate thread, need thread-safe async bridge
- **Queue**: Use asyncio.Queue to pass MIDI events to async LED controller

### GarageBand MIDI Setup
- GarageBand creates a virtual MIDI port when running
- Port name typically: "GarageBand" or similar
- User needs to enable MIDI output in GarageBand preferences
- May need to use IAC (Inter-Application Communication) driver on macOS

### MIDI Message Format
- **Note On**: `[0x90, note, velocity]` (channel 1, note 0-127, velocity 0-127)
- **Note Off**: `[0x80, note, velocity]` (or Note On with velocity 0)
- Focus on Note On events with velocity > 0 for drum hits

### LED Response Strategies
1. **Flash on Hit**: Brief bright flash, then fade
2. **Color per Drum**: Different colors for kick, snare, etc.
3. **Brightness by Velocity**: Harder hits = brighter lights
4. **Strobe Effect**: Rapid on/off for cymbals
5. **Pattern Trigger**: Trigger specific patterns on certain drums

## Configuration Options

### Drum-to-Color Mapping (Example)
```python
DRUM_COLORS = {
    "kick": (255, 0, 0),      # Red
    "snare": (255, 255, 255), # White
    "hihat": (0, 255, 255),   # Cyan
    "crash": (255, 255, 0),   # Yellow
    "ride": (255, 165, 0),    # Orange
    "tom": (0, 255, 0),       # Green
}
```

### MIDI Note Mappings (Standard GM Drum Kit)
```python
DRUM_NOTES = {
    36: "kick",      # Acoustic Bass Drum
    35: "kick",      # Electric Bass Drum
    38: "snare",     # Acoustic Snare
    40: "snare",     # Electric Snare
    42: "hihat",     # Closed Hi-Hat
    44: "hihat",     # Pedal Hi-Hat
    46: "hihat",     # Open Hi-Hat
    49: "crash",     # Crash Cymbal 1
    57: "crash",     # Crash Cymbal 2
    51: "ride",      # Ride Cymbal 1
    59: "ride",      # Ride Cymbal 2
    41: "tom",       # Low Floor Tom
    43: "tom",       # High Floor Tom
    45: "tom",       # Low Tom
    47: "tom",       # Low-Mid Tom
    48: "tom",       # Hi-Mid Tom
}
```

## File Structure
```
led/
├── __init__.py
├── discoverer.py          # (existing)
├── neon.py                # (existing - LEDController)
├── midi_handler.py        # (new - MIDI input)
├── drum_mapper.py         # (new - drum mapping)
└── midi_sync.py           # (new - main sync logic)
```

## Usage Flow
1. User starts GarageBand and loads a drum track
2. User runs: `midi-sync` (or CLI command)
3. Script lists available MIDI input ports
4. User selects GarageBand's MIDI port
5. Script scans for LEDDMX devices
6. User selects LED device
7. Script starts listening for MIDI events
8. On drum hit → LED responds in real-time
9. Ctrl+C to stop

## Error Handling
- MIDI port disconnection → attempt reconnection
- LED device disconnection → attempt reconnection
- Invalid MIDI messages → log and ignore
- Rate limiting → prevent LED command spam

## Future Enhancements
- Configuration file (YAML/JSON) for custom mappings
- Multiple LED devices support
- MIDI clock sync for tempo-based effects
- Recording/playback of MIDI-to-light sequences
- Web UI for real-time visualization
- Audio analysis fallback (if MIDI unavailable)

## Testing Strategy
1. Unit tests for drum mapping logic
2. Mock MIDI input for integration tests
3. Manual testing with GarageBand
4. Latency measurement tools
5. Stress testing with rapid drum hits

