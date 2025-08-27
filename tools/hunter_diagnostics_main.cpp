#include "../src/audio_diagnostics/audio_monitor.h"
#include <iostream>
#include <string>
#include <chrono>
#include <thread>

using namespace AudioDiagnostics;

void print_usage(const char* program_name) {
    std::cout << "Hunter: The Reckoning Audio Diagnostics Tool\n";
    std::cout << "Usage: " << program_name << " [options]\n\n";
    std::cout << "Options:\n";
    std::cout << "  --monitor              Start real-time audio monitoring\n";
    std::cout << "  --log-file FILE        Set log file path\n";
    std::cout << "  --analysis-interval MS Set analysis interval in milliseconds\n";
    std::cout << "  --export-channel N     Export channel N data to WAV file\n";
    std::cout << "  --help                 Show this help message\n\n";
    std::cout << "Examples:\n";
    std::cout << "  " << program_name << " --monitor --log-file hunter_debug.log\n";
    std::cout << "  " << program_name << " --export-channel 2\n";
}

int main(int argc, char* argv[]) {
    AudioChannelMonitor monitor;
    DirectSoundMonitor ds_monitor;
    bool start_monitoring = false;
    std::string log_file = "hunter_audio_debug.log";
    int analysis_interval_ms = 100;
    int export_channel = -1;
    
    // Parse command line arguments
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        else if (arg == "--monitor") {
            start_monitoring = true;
        }
        else if (arg == "--log-file" && i + 1 < argc) {
            log_file = argv[++i];
        }
        else if (arg == "--analysis-interval" && i + 1 < argc) {
            analysis_interval_ms = std::atoi(argv[++i]);
        }
        else if (arg == "--export-channel" && i + 1 < argc) {
            export_channel = std::atoi(argv[++i]);
        }
        else {
            std::cerr << "Unknown option: " << arg << "\n";
            print_usage(argv[0]);
            return 1;
        }
    }
    
    std::cout << "Hunter: The Reckoning Audio Diagnostics Tool\n";
    std::cout << "=============================================\n\n";
    
    // Set up monitor configuration
    monitor.setLogFile(log_file);
    monitor.setAnalysisInterval(std::chrono::milliseconds(analysis_interval_ms));
    
    if (export_channel >= 0) {
        std::cout << "Exporting channel " << export_channel << " data...\n";
        std::string filename = "channel_" + std::to_string(export_channel) + "_export.wav";
        monitor.exportChannelData(export_channel, filename);
        std::cout << "Export completed: " << filename << "\n";
        return 0;
    }
    
    if (start_monitoring) {
        std::cout << "Starting real-time audio monitoring...\n";
        std::cout << "Log file: " << log_file << "\n";
        std::cout << "Analysis interval: " << analysis_interval_ms << "ms\n\n";
        
        monitor.enableRealTimeAnalysis(true);
        
        std::cout << "Monitoring active. Press Ctrl+C to stop.\n";
        std::cout << "Expected Hunter: The Reckoning audio patterns:\n";
        std::cout << "- Fighting sounds: Channels 2-3, 1-4kHz range\n";
        std::cout << "- Menu sounds: Channel 1, 2-8kHz range\n";
        std::cout << "- Voice: Channel 0, 85-255Hz range\n\n";
        
        // Simulate monitoring loop (in real implementation, this would hook into xemu)
        auto start_time = std::chrono::steady_clock::now();
        
        while (true) {
            // In actual implementation, this would receive audio data from xemu
            // For now, we'll just demonstrate the monitoring capability
            
            auto current_time = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(current_time - start_time);
            
            if (elapsed.count() % 5 == 0) {
                // Periodic status update
                monitor.logAudioEvents();
                
                std::vector<int> missing = monitor.getMissingChannels();
                if (!missing.empty()) {
                    std::cout << "WARNING: Missing expected audio channels: ";
                    for (int ch : missing) {
                        std::cout << ch << " ";
                    }
                    std::cout << "\n";
                }
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    else {
        print_usage(argv[0]);
        std::cout << "\nNote: This tool needs to be integrated with xemu to capture live audio data.\n";
        std::cout << "For analysis of audio files, use the Python tool: hunter_audio_analyzer.py\n";
    }
    
    return 0;
}