#!/bin/bash

# Hunter: The Reckoning Audio Fix - Setup Script
# This script sets up the development environment for diagnosing and fixing
# the audio issues in Hunter: The Reckoning emulator

set -e

echo "Hunter: The Reckoning Audio Fix - Setup"
echo "======================================"

# Check if running on supported system
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This script is optimized for Linux. Some packages may need manual installation on other systems."
fi

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install build dependencies
echo "Installing build dependencies..."
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv

# Install audio libraries
echo "Installing audio development libraries..."
sudo apt-get install -y \
    libfftw3-dev \
    libopenal-dev \
    libsdl2-dev \
    libsndfile1-dev \
    libasound2-dev \
    portaudio19-dev

# Install audio tools
echo "Installing audio analysis tools..."
sudo apt-get install -y \
    audacity \
    sox \
    ffmpeg \
    pulseaudio-utils

# Create Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python audio analysis libraries..."
pip install --upgrade pip
pip install numpy scipy matplotlib seaborn
pip install librosa soundfile pyaudio
pip install scikit-learn pandas
pip install jupyter notebook  # For interactive analysis

# Create necessary directories
echo "Creating project directories..."
mkdir -p build
mkdir -p logs
mkdir -p test_audio
mkdir -p analysis_output

# Build the project
echo "Building audio diagnostics tools..."
cd build
cmake ..
make -j$(nproc)
cd ..

# Set up Git hooks for development
echo "Setting up Git hooks..."
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to run basic checks

echo "Running pre-commit checks..."

# Check for Python syntax errors
python3 -m py_compile src/audio_analysis/hunter_audio_analyzer.py

# Check C++ compilation
cd build && make -j$(nproc) && cd ..

echo "Pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit

# Create configuration file
echo "Creating configuration file..."
cat > config.json << 'EOF'
{
    "audio_settings": {
        "sample_rate": 44100,
        "buffer_size": 1024,
        "analysis_window_ms": 100
    },
    "hunter_patterns": {
        "fighting_sounds": {
            "frequency_range": [1000, 4000],
            "expected_channels": [2, 3],
            "min_duration_ms": 50
        },
        "menu_sounds": {
            "frequency_range": [2000, 8000],
            "expected_channels": [1],
            "min_duration_ms": 20
        }
    },
    "paths": {
        "log_directory": "logs",
        "analysis_output": "analysis_output",
        "test_audio": "test_audio"
    }
}
EOF

# Create wrapper scripts
echo "Creating wrapper scripts..."

# Python analyzer wrapper
cat > run_audio_analysis.sh << 'EOF'
#!/bin/bash
# Wrapper script for the Python audio analyzer

source venv/bin/activate
python3 src/audio_analysis/hunter_audio_analyzer.py "$@"
EOF

chmod +x run_audio_analysis.sh

# C++ diagnostics wrapper
cat > run_diagnostics.sh << 'EOF'
#!/bin/bash
# Wrapper script for the C++ diagnostics tool

if [ ! -f build/hunter_audio_diagnostics ]; then
    echo "Error: Diagnostics tool not built. Run setup.sh first."
    exit 1
fi

./build/hunter_audio_diagnostics "$@"
EOF

chmod +x run_diagnostics.sh

# Create test script
cat > test_setup.sh << 'EOF'
#!/bin/bash
# Test script to verify setup

echo "Testing setup..."

# Test Python environment
echo "Testing Python environment..."
source venv/bin/activate
python3 -c "import librosa; import numpy; import sklearn; print('Python dependencies OK')"

# Test C++ build
echo "Testing C++ build..."
if [ -f build/hunter_audio_diagnostics ]; then
    echo "C++ build OK"
else
    echo "Error: C++ build failed"
    exit 1
fi

# Test audio system
echo "Testing audio system..."
if command -v aplay &> /dev/null; then
    echo "Audio system OK"
else
    echo "Warning: Audio system may not be properly configured"
fi

echo "Setup test completed successfully!"
EOF

chmod +x test_setup.sh

# Create README for quick start
cat > QUICK_START.md << 'EOF'
# Quick Start Guide

## Running the Setup
```bash
./setup.sh
```

## Testing the Installation
```bash
./test_setup.sh
```

## Using the Audio Analyzer

### Python AI Analysis Tool
```bash
./run_audio_analysis.sh --reference reference_audio.wav --emulated emulated_audio.wav --visualize
```

### C++ Diagnostics Tool
```bash
./run_diagnostics.sh --monitor --log-file logs/audio_debug.log
```

## Integration with xemu

1. Build xemu with audio debugging enabled
2. Capture audio streams during Hunter: The Reckoning gameplay
3. Run analysis tools to identify missing patterns
4. Apply fixes based on analysis results

## Directory Structure
- `src/` - Source code
- `build/` - Compiled binaries
- `logs/` - Debug logs
- `test_audio/` - Audio test files
- `analysis_output/` - Analysis results
EOF

echo ""
echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run './test_setup.sh' to verify installation"
echo "2. Read QUICK_START.md for usage instructions"
echo "3. Capture audio from Hunter: The Reckoning for analysis"
echo "4. Run analysis tools to identify audio issues"
echo ""
echo "For xemu integration, see the research document:"
echo "HUNTER_RECKONING_AUDIO_RESEARCH.md"