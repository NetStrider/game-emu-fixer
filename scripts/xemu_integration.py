#!/usr/bin/env python3
"""
xemu integration helper for Hunter: The Reckoning audio analysis
This script provides utilities for integrating with the xemu emulator
"""

import subprocess
import os
import shutil
import json
from pathlib import Path
import tempfile

class XemuIntegration:
    """Helper class for xemu integration"""
    
    def __init__(self, xemu_path=None):
        self.xemu_path = xemu_path or self.find_xemu()
        self.temp_dir = tempfile.mkdtemp(prefix="hunter_audio_")
        
    def find_xemu(self):
        """Attempt to locate xemu installation"""
        
        # Common xemu paths
        possible_paths = [
            "/usr/local/bin/xemu",
            "/usr/bin/xemu",
            "~/xemu/build/xemu",
            "./xemu",
            shutil.which("xemu")
        ]
        
        for path in possible_paths:
            if path and os.path.exists(os.path.expanduser(path)):
                return os.path.expanduser(path)
        
        print("Warning: xemu not found in common locations")
        print("Please specify xemu path manually or install xemu")
        return None
    
    def patch_xemu_for_audio_capture(self):
        """Generate patch for xemu to enable audio capture"""
        
        patch_content = '''
// Hunter: The Reckoning Audio Capture Patch
// Add this to xemu's audio output function

#include <fstream>
#include <vector>

static std::ofstream hunter_audio_log("hunter_audio_capture.log");
static bool hunter_capture_enabled = false;

void enable_hunter_audio_capture() {
    hunter_capture_enabled = true;
    hunter_audio_log << "Hunter audio capture enabled\\n";
}

void capture_hunter_audio(int channel, const void* data, size_t length, 
                         uint32_t sample_rate, uint16_t channels) {
    if (!hunter_capture_enabled) return;
    
    // Log audio data for analysis
    hunter_audio_log << "Channel: " << channel 
                     << " Length: " << length 
                     << " SampleRate: " << sample_rate 
                     << " Channels: " << channels << std::endl;
    
    // Save audio data to temporary file for analysis
    static int frame_counter = 0;
    if (frame_counter % 100 == 0) { // Sample every 100 frames
        std::string filename = "hunter_audio_frame_" + std::to_string(frame_counter) + ".raw";
        std::ofstream audio_file(filename, std::ios::binary);
        audio_file.write(static_cast<const char*>(data), length);
    }
    frame_counter++;
}

// Add this call to the main audio output function:
// capture_hunter_audio(channel_id, audio_buffer, buffer_size, sample_rate, num_channels);
'''
        
        patch_file = os.path.join(self.temp_dir, "hunter_audio_patch.cpp")
        with open(patch_file, 'w') as f:
            f.write(patch_content)
        
        print(f"Audio capture patch generated: {patch_file}")
        print("\nTo apply this patch to xemu:")
        print("1. Locate xemu's audio output function (likely in audio.c or similar)")
        print("2. Add the capture function and enable call")
        print("3. Rebuild xemu with the patch")
        
        return patch_file
    
    def create_xemu_config(self, game_iso_path, enable_audio_debug=True):
        """Create xemu configuration for Hunter: The Reckoning"""
        
        config = {
            "general": {
                "show_welcome": False,
                "check_for_updates": False
            },
            "audio": {
                "driver": "directsound",
                "buffer_size": 1024,
                "sample_rate": 44100,
                "debug_logging": enable_audio_debug
            },
            "input": {
                "controller_1_type": "xbox_controller"
            },
            "display": {
                "resolution_scale": 1,
                "vsync": True
            },
            "system": {
                "memory_limit_mb": 128,
                "cpu_throttle": False
            }
        }
        
        config_file = os.path.join(self.temp_dir, "xemu_hunter_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"xemu configuration created: {config_file}")
        return config_file
    
    def generate_run_script(self, game_iso_path, config_file=None):
        """Generate script to run Hunter: The Reckoning with audio capture"""
        
        if not self.xemu_path:
            print("Error: xemu path not found")
            return None
        
        script_content = f'''#!/bin/bash

# Hunter: The Reckoning Audio Analysis Run Script
# Generated automatically for audio debugging

echo "Starting Hunter: The Reckoning with audio analysis..."

# Set environment variables for audio debugging
export XEMU_AUDIO_DEBUG=1
export HUNTER_AUDIO_CAPTURE=1

# Create log directory
mkdir -p logs

# Start xemu with Hunter: The Reckoning
{self.xemu_path} \\
    -dvd_path "{game_iso_path}" \\
    -config_path "{config_file or 'default'}" \\
    -debug_audio \\
    2>&1 | tee logs/xemu_hunter_session.log

echo "Session completed. Check logs/ directory for audio capture data."
'''
        
        script_file = os.path.join(self.temp_dir, "run_hunter_with_capture.sh")
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_file, 0o755)  # Make executable
        
        print(f"Run script generated: {script_file}")
        return script_file
    
    def extract_audio_from_logs(self, log_dir="logs"):
        """Extract audio data from xemu logs for analysis"""
        
        log_files = Path(log_dir).glob("*.log")
        audio_events = []
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f):
                    if "Hunter audio capture" in line or "DirectSound" in line:
                        audio_events.append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip(),
                            "timestamp": self.extract_timestamp(line)
                        })
        
        # Save extracted events
        events_file = os.path.join(self.temp_dir, "hunter_audio_events.json")
        with open(events_file, 'w') as f:
            json.dump(audio_events, f, indent=2)
        
        print(f"Extracted {len(audio_events)} audio events to {events_file}")
        return events_file
    
    def extract_timestamp(self, log_line):
        """Extract timestamp from log line"""
        # Simple timestamp extraction (adjust based on xemu log format)
        if '[' in log_line and ']' in log_line:
            start = log_line.find('[') + 1
            end = log_line.find(']')
            return log_line[start:end]
        return None
    
    def generate_integration_guide(self):
        """Generate step-by-step integration guide"""
        
        guide = '''
# xemu Integration Guide for Hunter: The Reckoning Audio Analysis

## Prerequisites
1. xemu emulator installed and working
2. Hunter: The Reckoning ISO/disc image
3. This audio analysis toolkit

## Step 1: Prepare xemu for Audio Capture

### Option A: Use Pre-built Audio Hooks (Recommended)
1. Download the modified xemu build with audio hooks
2. Extract to your preferred location
3. Verify it works with a test game

### Option B: Build from Source with Patches
1. Clone xemu source code:
   ```bash
   git clone https://github.com/xemu-project/xemu.git
   cd xemu
   ```

2. Apply the audio capture patch (generated by this script)

3. Build xemu:
   ```bash
   ./build.sh
   ```

## Step 2: Capture Audio Data

1. Run the generated script:
   ```bash
   ./run_hunter_with_capture.sh
   ```

2. Play Hunter: The Reckoning, focusing on areas with missing audio:
   - Main menu (listen for selection sounds)
   - Combat scenes (listen for missing fighting sounds)
   - Character movement (footsteps, interactions)

3. Stop the capture after 5-10 minutes of gameplay

## Step 3: Analyze Captured Audio

1. Extract audio events from logs:
   ```bash
   python3 scripts/xemu_integration.py extract-logs
   ```

2. Run the audio analysis:
   ```bash
   ./run_audio_analysis.sh --emulated captured_audio.wav --reference reference_audio.wav
   ```

3. Review the analysis results and recommendations

## Step 4: Apply Fixes

Based on the analysis results, apply appropriate fixes:

1. DirectSound buffer issues → Fix buffer management in xemu
2. Missing audio channels → Add channel routing
3. Timing issues → Adjust audio synchronization

## Troubleshooting

### No Audio Captured
- Verify xemu audio output is working
- Check audio capture patch is applied correctly
- Ensure Hunter: The Reckoning is using the problematic audio paths

### Analysis Fails
- Check audio file formats are correct
- Verify Python dependencies are installed
- Review analysis tool logs for specific errors

### Integration Issues
- Ensure xemu modifications don't break other games
- Test with multiple audio devices
- Verify timing-sensitive code changes
'''
        
        guide_file = os.path.join(self.temp_dir, "XEMU_INTEGRATION_GUIDE.md")
        with open(guide_file, 'w') as f:
            f.write(guide)
        
        print(f"Integration guide created: {guide_file}")
        return guide_file
    
    def cleanup(self):
        """Clean up temporary files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="xemu integration helper for Hunter: The Reckoning audio analysis"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate patch
    patch_parser = subparsers.add_parser('generate-patch', 
                                        help='Generate audio capture patch for xemu')
    
    # Create config
    config_parser = subparsers.add_parser('create-config',
                                         help='Create xemu configuration')
    config_parser.add_argument('--game-iso', required=True,
                              help='Path to Hunter: The Reckoning ISO')
    
    # Generate run script
    script_parser = subparsers.add_parser('generate-script',
                                         help='Generate run script')
    script_parser.add_argument('--game-iso', required=True,
                              help='Path to Hunter: The Reckoning ISO')
    script_parser.add_argument('--xemu-path',
                              help='Path to xemu executable')
    
    # Extract logs
    extract_parser = subparsers.add_parser('extract-logs',
                                          help='Extract audio events from logs')
    extract_parser.add_argument('--log-dir', default='logs',
                               help='Directory containing xemu logs')
    
    # Generate guide
    guide_parser = subparsers.add_parser('generate-guide',
                                        help='Generate integration guide')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    integration = XemuIntegration(getattr(args, 'xemu_path', None))
    
    try:
        if args.command == 'generate-patch':
            integration.patch_xemu_for_audio_capture()
        
        elif args.command == 'create-config':
            integration.create_xemu_config(args.game_iso)
        
        elif args.command == 'generate-script':
            config_file = integration.create_xemu_config(args.game_iso)
            integration.generate_run_script(args.game_iso, config_file)
        
        elif args.command == 'extract-logs':
            integration.extract_audio_from_logs(args.log_dir)
        
        elif args.command == 'generate-guide':
            integration.generate_integration_guide()
        
        print(f"\nTemporary files location: {integration.temp_dir}")
        print("Use 'cleanup' to remove temporary files when done.")
        
    except Exception as e:
        print(f"Error: {e}")
        integration.cleanup()

if __name__ == "__main__":
    main()