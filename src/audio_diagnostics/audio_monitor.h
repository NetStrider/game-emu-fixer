#pragma once

#include <map>
#include <vector>
#include <memory>
#include <chrono>
#include <fstream>
#include <mutex>

namespace AudioDiagnostics {

struct AudioStreamData {
    std::vector<float> samples;
    std::chrono::high_resolution_clock::time_point timestamp;
    uint32_t sample_rate;
    uint16_t channels;
    uint16_t bit_depth;
    bool is_active;
};

struct FrequencyBin {
    float frequency;
    float magnitude;
    float phase;
};

class FrequencyAnalyzer {
public:
    FrequencyAnalyzer(size_t fft_size = 1024);
    ~FrequencyAnalyzer();
    
    std::vector<FrequencyBin> analyze(const std::vector<float>& samples);
    void detectMissingFrequencies(const std::vector<FrequencyBin>& reference, 
                                 const std::vector<FrequencyBin>& current);
    
private:
    size_t fft_size_;
    void* fft_plan_;  // FFTW plan
    float* input_buffer_;
    float* output_buffer_;
};

class AudioChannelMonitor {
public:
    AudioChannelMonitor();
    ~AudioChannelMonitor();
    
    // Core monitoring functions
    void captureAudioStream(int channel, const void* data, size_t length, 
                           uint32_t sample_rate, uint16_t channels, uint16_t bit_depth);
    void analyzeFrequencySpectrum(int channel);
    void detectMissingChannels();
    void logAudioEvents();
    
    // Analysis functions
    bool isChannelActive(int channel) const;
    float getChannelVolume(int channel) const;
    std::vector<int> getMissingChannels() const;
    
    // Configuration
    void setLogFile(const std::string& filename);
    void enableRealTimeAnalysis(bool enable);
    void setAnalysisInterval(std::chrono::milliseconds interval);
    
    // Export functions
    void exportChannelData(int channel, const std::string& filename);
    void exportFrequencyAnalysis(int channel, const std::string& filename);
    
private:
    std::map<int, AudioStreamData> channels_;
    std::unique_ptr<FrequencyAnalyzer> analyzer_;
    std::ofstream log_file_;
    std::mutex data_mutex_;
    
    bool real_time_analysis_enabled_;
    std::chrono::milliseconds analysis_interval_;
    std::chrono::high_resolution_clock::time_point last_analysis_;
    
    // Helper functions
    void updateChannelActivity();
    void writeLogEntry(const std::string& message);
    std::vector<float> convertToFloat(const void* data, size_t length, uint16_t bit_depth);
};

// Hunter: The Reckoning specific audio patterns
class HunterAudioPatterns {
public:
    struct SoundPattern {
        std::string name;
        std::vector<FrequencyBin> frequency_signature;
        float duration_ms;
        float expected_volume;
        int expected_channel;
    };
    
    static std::vector<SoundPattern> getFightingSoundPatterns();
    static std::vector<SoundPattern> getMenuSoundPatterns();
    static std::vector<SoundPattern> getVoiceoverPatterns();
    
    bool detectPattern(const SoundPattern& pattern, 
                      const std::vector<FrequencyBin>& current_spectrum);
    
private:
    static const float PATTERN_MATCH_THRESHOLD;
};

// Xbox DirectSound emulation monitor
class DirectSoundMonitor {
public:
    struct DSBufferInfo {
        uint32_t buffer_id;
        uint32_t size;
        uint32_t format;
        bool is_3d;
        bool is_primary;
        bool is_playing;
        float volume;
        uint32_t frequency;
    };
    
    void registerBuffer(uint32_t buffer_id, const DSBufferInfo& info);
    void updateBufferState(uint32_t buffer_id, bool playing, float volume);
    void logAPICall(const std::string& function_name, const std::vector<std::string>& params);
    
    std::vector<DSBufferInfo> getActiveBuffers() const;
    std::vector<DSBufferInfo> getMissingExpectedBuffers() const;
    
private:
    std::map<uint32_t, DSBufferInfo> buffers_;
    std::vector<std::string> api_call_log_;
    std::mutex buffer_mutex_;
};

} // namespace AudioDiagnostics