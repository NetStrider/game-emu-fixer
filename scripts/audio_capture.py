#!/usr/bin/env python3
"""
Audio capture utility for Hunter: The Reckoning
This script helps capture audio from various sources for analysis
"""

import pyaudio
import wave
import numpy as np
import time
import argparse
from pathlib import Path

class AudioCapture:
    def __init__(self, sample_rate=44100, channels=2, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.recording = False
        
    def list_devices(self):
        """List available audio devices"""
        print("Available audio devices:")
        print("-" * 50)
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            print(f"Device {i}: {info['name']}")
            print(f"  Max input channels: {info['maxInputChannels']}")
            print(f"  Max output channels: {info['maxOutputChannels']}")
            print(f"  Default sample rate: {info['defaultSampleRate']}")
            print()
    
    def capture_audio(self, duration_seconds, output_file, device_index=None):
        """Capture audio for specified duration"""
        
        print(f"Recording for {duration_seconds} seconds...")
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Channels: {self.channels}")
        print(f"Output file: {output_file}")
        
        # Open stream
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        
        frames = []
        
        try:
            for i in range(0, int(self.sample_rate / self.chunk_size * duration_seconds)):
                data = stream.read(self.chunk_size)
                frames.append(data)
                
                # Progress indicator
                if i % 20 == 0:
                    elapsed = i * self.chunk_size / self.sample_rate
                    print(f"\rRecording... {elapsed:.1f}s / {duration_seconds}s", end='')
        
        except KeyboardInterrupt:
            print("\nRecording interrupted by user")
        
        finally:
            stream.stop_stream()
            stream.close()
        
        print(f"\nSaving to {output_file}...")
        
        # Save to WAV file
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        print("Recording saved successfully!")
    
    def monitor_audio_levels(self, device_index=None, duration=10):
        """Monitor audio levels for debugging"""
        
        print(f"Monitoring audio levels for {duration} seconds...")
        print("Press Ctrl+C to stop early")
        
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        
        try:
            start_time = time.time()
            while time.time() - start_time < duration:
                data = stream.read(self.chunk_size)
                
                # Convert to numpy array and calculate RMS
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                
                # Convert to dB
                if rms > 0:
                    db = 20 * np.log10(rms / 32768.0)
                else:
                    db = -np.inf
                
                # Create visual level meter
                level_bars = int((db + 60) / 3)  # Scale from -60dB to 0dB
                level_bars = max(0, min(20, level_bars))
                
                meter = "█" * level_bars + "░" * (20 - level_bars)
                print(f"\rLevel: [{meter}] {db:6.1f} dB", end='')
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        
        finally:
            stream.stop_stream()
            stream.close()
    
    def __del__(self):
        if hasattr(self, 'audio'):
            self.audio.terminate()

def main():
    parser = argparse.ArgumentParser(
        description="Audio capture utility for Hunter: The Reckoning analysis"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List devices command
    list_parser = subparsers.add_parser('list', help='List available audio devices')
    
    # Record command
    record_parser = subparsers.add_parser('record', help='Record audio')
    record_parser.add_argument('--duration', type=int, default=30,
                              help='Recording duration in seconds (default: 30)')
    record_parser.add_argument('--output', required=True,
                              help='Output WAV file path')
    record_parser.add_argument('--device', type=int,
                              help='Input device index (use list command to see options)')
    record_parser.add_argument('--sample-rate', type=int, default=44100,
                              help='Sample rate (default: 44100)')
    record_parser.add_argument('--channels', type=int, default=2,
                              help='Number of channels (default: 2)')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor audio levels')
    monitor_parser.add_argument('--device', type=int,
                               help='Input device index')
    monitor_parser.add_argument('--duration', type=int, default=10,
                               help='Monitoring duration in seconds (default: 10)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        capture = AudioCapture()
        capture.list_devices()
    
    elif args.command == 'record':
        capture = AudioCapture(
            sample_rate=args.sample_rate,
            channels=args.channels
        )
        
        # Create output directory if needed
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        
        capture.capture_audio(args.duration, args.output, args.device)
    
    elif args.command == 'monitor':
        capture = AudioCapture()
        capture.monitor_audio_levels(args.device, args.duration)

if __name__ == "__main__":
    main()