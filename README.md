# Snare Flare 🥁💡

Real-time MIDI drum input to LED light synchronization. Transform your drum performances with dynamic visual effects that respond to every hit in real-time.

## Features

- 🎵 **Real-time MIDI Processing**: Ultra-low latency MIDI event processing from drum kits or DAWs
- 💡 **LED Control**: Synchronize LEDDMX-00 Bluetooth LED devices with drum hits
- 🎨 **Color Mapping**: Automatic color assignment per drum type (kick=red, snare=white, etc.)
- ⚡ **Velocity Sensitivity**: LED brightness responds to hit velocity
- 🥁 **Drum Detection**: Supports standard General MIDI (GM) drum kit mappings
- 🔄 **Smart Queue Management**: Drops stale events to maintain low latency
- 🎯 **Kick Prioritization**: Kicks get priority processing for maximum impact

## Requirements

- Python 3.8+
- macOS (for CoreMIDI support)
- LEDDMX-00 Bluetooth LED device
- MIDI input source (drum kit, GarageBand, or other MIDI source)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd led
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

## Usage

### Basic Usage

1. **Start your MIDI source** (drum kit, GarageBand, etc.)

2. **Run snare-flare:**
   ```bash
   midi-sync
   ```

3. **Select your MIDI input port** when prompted (or it will auto-detect hardware devices)

4. **Select your LED device** when prompted

5. **Start playing!** Hit your drums and watch the lights respond in real-time.

### Command-Line Options

```bash
midi-sync [OPTIONS]
```

**Options:**

- `--midi-port PORT`: Specify MIDI input port name (auto-detects if not specified)
- `--led-address ADDRESS`: Specify LED device Bluetooth address (prompts if not specified)
- `--flash-duration SECONDS`: Duration in seconds for flash effect (default: 0.05)
- `--max-event-age SECONDS`: Maximum age in seconds for events to be processed (default: 1.0)
  - Events older than this will be skipped to maintain low latency
- `-v, --verbose`: Enable verbose logging (shows all MIDI messages)
- `--test-midi`: Test mode - just listen to MIDI and print events (no LED control)

### Examples

**Basic sync:**
```bash
midi-sync
```

**Lower latency (drop events older than 0.5 seconds):**
```bash
midi-sync --max-event-age 0.5
```

**Longer flash duration:**
```bash
midi-sync --flash-duration 0.15
```

**Test MIDI input only:**
```bash
midi-sync --test-midi -v
```

**Specify devices explicitly:**
```bash
midi-sync --midi-port "Alesis Nitro Max" --led-address "XX:XX:XX:XX:XX:XX"
```

## Drum Mapping

The following MIDI notes are automatically mapped to colors:

| Drum | MIDI Notes | Color |
|------|------------|-------|
| Kick | 35, 36 | 🔴 Red |
| Snare | 38, 40 | ⚪ White |
| Hi-Hat | 42, 44, 46 | 🔵 Cyan |
| Crash | 49, 57 | 🟡 Yellow |
| Ride | 51, 59 | 🟠 Orange |
| Toms | 41, 43, 45, 47, 48, 50 | 🟢 Green |

Brightness is automatically adjusted based on MIDI velocity (0-127).

## MIDI Setup

### Direct Hardware Connection

Connect your drum kit directly via USB-MIDI. The app will auto-detect hardware MIDI devices and prioritize them over virtual ports.

### GarageBand Setup

If using GarageBand, you may need to set up MIDI routing:

1. **Option A: Use IAC Driver (Recommended)**
   - Open **Audio MIDI Setup** (Applications > Utilities)
   - Window → Show MIDI Studio
   - Double-click **IAC Driver**
   - Check **"Device is online"**
   - In GarageBand, route your drum track's MIDI output to "IAC Driver Bus 1"
   - Run `midi-sync` and select the IAC port

2. **Option B: Use GarageBand Virtual Out**
   - Ensure GarageBand is running
   - GarageBand creates a "GarageBand Virtual Out" port automatically
   - Select this port when prompted

## Troubleshooting

### No MIDI events detected

1. **Check MIDI port selection:**
   - Run with `-v` flag to see all MIDI messages
   - Verify the correct port is selected
   - Try `--test-midi` mode to verify MIDI input

2. **Verify MIDI routing:**
   - Ensure your MIDI source is sending events
   - Check GarageBand MIDI output settings if applicable
   - Try the IAC driver method for GarageBand

### LED not responding

1. **Check Bluetooth connection:**
   - Verify LED device is powered on and in range
   - Try disconnecting and reconnecting
   - Check device address is correct

2. **Check event processing:**
   - Run with `-v` to see if events are being processed
   - Look for "Processing MIDI event" messages in logs
   - Verify events aren't being skipped due to age (check `--max-event-age`)

### High latency

1. **Reduce event age threshold:**
   ```bash
   midi-sync --max-event-age 0.3
   ```

2. **Reduce flash duration:**
   ```bash
   midi-sync --flash-duration 0.03
   ```

3. **Check system load:**
   - Close other applications
   - Ensure Bluetooth connection is stable

## Project Structure

```
led/
├── led/
│   ├── __init__.py
│   ├── discoverer.py      # BLE device discovery
│   ├── neon.py            # LEDDMX-00 controller
│   ├── midi_handler.py    # MIDI input handling
│   ├── drum_mapper.py     # Drum-to-color mapping
│   └── midi_sync.py       # Main sync orchestrator
├── pyproject.toml
└── README.md
```

## Development

### Running Tests

Test MIDI input without LED control:
```bash
midi-sync --test-midi -v
```

### Verbose Logging

Enable detailed logging to debug issues:
```bash
midi-sync -v
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Acknowledgments

- Built with [mido](https://github.com/mido/mido) for MIDI handling
- Uses [bleak](https://github.com/hbldh/bleak) for Bluetooth Low Energy communication
- LEDDMX-00 protocol based on [LEDDMX-00](https://github.com/user154lt/LEDDMX-00)

