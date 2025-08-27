#include "audio_monitor.h"
#include <cstring>
#include <cmath>
#include <algorithm>
#include <sstream>
#include <fftw3.h>

namespace AudioDiagnostics {

// FrequencyAnalyzer Implementation
FrequencyAnalyzer::FrequencyAnalyzer(size_t fft_size) : fft_size_(fft_size) {
    input_buffer_ = (float*)fftwf_malloc(sizeof(float) * fft_size_);
    output_buffer_ = (float*)fftwf_malloc(sizeof(float) * fft_size_);
    
    fft_plan_ = fftwf_plan_r2r_1d(fft_size_, input_buffer_, output_buffer_,
                                  FFTW_R2HC, FFTW_ESTIMATE);
}

FrequencyAnalyzer::~FrequencyAnalyzer() {
    fftwf_destroy_plan((fftwf_plan)fft_plan_);
    fftwf_free(input_buffer_);
    fftwf_free(output_buffer_);
}

std::vector<FrequencyBin> FrequencyAnalyzer::analyze(const std::vector<float>& samples) {
    std::vector<FrequencyBin> bins;
    
    if (samples.size() < fft_size_) {
        return bins; // Not enough samples
    }
    
    // Copy samples to input buffer
    size_t start_idx = samples.size() - fft_size_;
    std::memcpy(input_buffer_, &samples[start_idx], sizeof(float) * fft_size_);
    
    // Apply window function (Hanning)
    for (size_t i = 0; i < fft_size_; ++i) {
        float window = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / (fft_size_ - 1)));
        input_buffer_[i] *= window;
    }
    
    // Execute FFT
    fftwf_execute((fftwf_plan)fft_plan_);
    
    // Convert to frequency bins
    bins.reserve(fft_size_ / 2);
    
    for (size_t i = 0; i < fft_size_ / 2; ++i) {
        FrequencyBin bin;
        bin.frequency = static_cast<float>(i) * 44100.0f / fft_size_; // Assuming 44.1kHz
        
        if (i == 0) {
            bin.magnitude = std::abs(output_buffer_[0]);
            bin.phase = 0.0f;
        } else if (i == fft_size_ / 2) {
            bin.magnitude = std::abs(output_buffer_[fft_size_ / 2]);
            bin.phase = 0.0f;
        } else {
            float real = output_buffer_[i];
            float imag = output_buffer_[fft_size_ - i];
            bin.magnitude = std::sqrt(real * real + imag * imag);
            bin.phase = std::atan2(imag, real);
        }
        
        bins.push_back(bin);
    }
    
    return bins;
}

void FrequencyAnalyzer::detectMissingFrequencies(const std::vector<FrequencyBin>& reference,
                                                const std::vector<FrequencyBin>& current) {
    // Implementation for detecting missing frequency components
    // This would compare reference vs current and identify gaps
}

// AudioChannelMonitor Implementation
AudioChannelMonitor::AudioChannelMonitor() 
    : analyzer_(std::make_unique<FrequencyAnalyzer>())
    , real_time_analysis_enabled_(false)
    , analysis_interval_(std::chrono::milliseconds(100))
    , last_analysis_(std::chrono::high_resolution_clock::now()) {
}

AudioChannelMonitor::~AudioChannelMonitor() {
    if (log_file_.is_open()) {
        log_file_.close();
    }
}

void AudioChannelMonitor::captureAudioStream(int channel, const void* data, size_t length,
                                           uint32_t sample_rate, uint16_t channels, uint16_t bit_depth) {
    std::lock_guard<std::mutex> lock(data_mutex_);
    
    AudioStreamData& stream = channels_[channel];
    stream.timestamp = std::chrono::high_resolution_clock::now();
    stream.sample_rate = sample_rate;
    stream.channels = channels;
    stream.bit_depth = bit_depth;
    stream.is_active = true;
    
    // Convert audio data to float samples
    std::vector<float> new_samples = convertToFloat(data, length, bit_depth);
    
    // Append to existing samples (keep rolling buffer)
    stream.samples.insert(stream.samples.end(), new_samples.begin(), new_samples.end());
    
    // Keep only last 5 seconds of audio
    size_t max_samples = sample_rate * 5;
    if (stream.samples.size() > max_samples) {
        stream.samples.erase(stream.samples.begin(), 
                           stream.samples.begin() + (stream.samples.size() - max_samples));
    }
    
    // Log the capture event
    std::ostringstream oss;
    oss << "Channel " << channel << ": Captured " << length << " bytes, "
        << new_samples.size() << " samples at " << sample_rate << "Hz";
    writeLogEntry(oss.str());
    
    // Trigger real-time analysis if enabled
    if (real_time_analysis_enabled_) {
        auto now = std::chrono::high_resolution_clock::now();
        if (now - last_analysis_ >= analysis_interval_) {
            analyzeFrequencySpectrum(channel);
            last_analysis_ = now;
        }
    }
}

void AudioChannelMonitor::analyzeFrequencySpectrum(int channel) {
    std::lock_guard<std::mutex> lock(data_mutex_);
    
    auto it = channels_.find(channel);
    if (it == channels_.end() || it->second.samples.empty()) {
        return;
    }
    
    std::vector<FrequencyBin> spectrum = analyzer_->analyze(it->second.samples);
    
    // Log significant frequency components
    std::ostringstream oss;
    oss << "Channel " << channel << " spectrum: ";
    
    for (const auto& bin : spectrum) {
        if (bin.magnitude > 0.01f) { // Only log significant components
            oss << bin.frequency << "Hz(" << bin.magnitude << ") ";
        }
    }
    
    writeLogEntry(oss.str());
}

void AudioChannelMonitor::detectMissingChannels() {
    std::lock_guard<std::mutex> lock(data_mutex_);
    
    // Hunter: The Reckoning expected channels
    std::vector<int> expected_channels = {0, 1, 2, 3, 4, 5}; // Based on typical Xbox game audio setup
    
    std::vector<int> missing;
    for (int expected : expected_channels) {
        auto it = channels_.find(expected);
        if (it == channels_.end() || !it->second.is_active) {
            missing.push_back(expected);
        }
    }
    
    if (!missing.empty()) {
        std::ostringstream oss;
        oss << "Missing audio channels: ";
        for (int ch : missing) {
            oss << ch << " ";
        }
        writeLogEntry(oss.str());
    }
}

void AudioChannelMonitor::logAudioEvents() {
    updateChannelActivity();
    detectMissingChannels();
    
    // Log current channel status
    std::ostringstream oss;
    oss << "Active channels: ";
    
    for (const auto& pair : channels_) {
        if (pair.second.is_active) {
            oss << pair.first << "(" << getChannelVolume(pair.first) << ") ";
        }
    }
    
    writeLogEntry(oss.str());
}

bool AudioChannelMonitor::isChannelActive(int channel) const {
    std::lock_guard<std::mutex> lock(data_mutex_);
    auto it = channels_.find(channel);
    return it != channels_.end() && it->second.is_active;
}

float AudioChannelMonitor::getChannelVolume(int channel) const {
    std::lock_guard<std::mutex> lock(data_mutex_);
    auto it = channels_.find(channel);
    if (it == channels_.end() || it->second.samples.empty()) {
        return 0.0f;
    }
    
    // Calculate RMS volume
    float sum_squares = 0.0f;
    const auto& samples = it->second.samples;
    size_t sample_count = std::min(samples.size(), static_cast<size_t>(it->second.sample_rate / 10)); // Last 100ms
    
    for (size_t i = samples.size() - sample_count; i < samples.size(); ++i) {
        sum_squares += samples[i] * samples[i];
    }
    
    return std::sqrt(sum_squares / sample_count);
}

std::vector<int> AudioChannelMonitor::getMissingChannels() const {
    std::vector<int> expected_channels = {0, 1, 2, 3, 4, 5};
    std::vector<int> missing;
    
    for (int expected : expected_channels) {
        if (!isChannelActive(expected)) {
            missing.push_back(expected);
        }
    }
    
    return missing;
}

void AudioChannelMonitor::setLogFile(const std::string& filename) {
    if (log_file_.is_open()) {
        log_file_.close();
    }
    
    log_file_.open(filename, std::ios::app);
    writeLogEntry("=== Audio monitoring session started ===");
}

void AudioChannelMonitor::enableRealTimeAnalysis(bool enable) {
    real_time_analysis_enabled_ = enable;
    writeLogEntry(enable ? "Real-time analysis enabled" : "Real-time analysis disabled");
}

void AudioChannelMonitor::setAnalysisInterval(std::chrono::milliseconds interval) {
    analysis_interval_ = interval;
}

void AudioChannelMonitor::exportChannelData(int channel, const std::string& filename) {
    std::lock_guard<std::mutex> lock(data_mutex_);
    
    auto it = channels_.find(channel);
    if (it == channels_.end()) {
        return;
    }
    
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return;
    }
    
    // Write WAV header
    // ... WAV file format implementation ...
    
    // Write sample data
    for (float sample : it->second.samples) {
        int16_t sample_16 = static_cast<int16_t>(sample * 32767.0f);
        file.write(reinterpret_cast<const char*>(&sample_16), sizeof(sample_16));
    }
}

void AudioChannelMonitor::updateChannelActivity() {
    auto now = std::chrono::high_resolution_clock::now();
    const auto timeout = std::chrono::milliseconds(500); // 500ms timeout
    
    for (auto& pair : channels_) {
        if (now - pair.second.timestamp > timeout) {
            pair.second.is_active = false;
        }
    }
}

void AudioChannelMonitor::writeLogEntry(const std::string& message) {
    if (log_file_.is_open()) {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        
        log_file_ << "[" << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S") << "] "
                  << message << std::endl;
        log_file_.flush();
    }
}

std::vector<float> AudioChannelMonitor::convertToFloat(const void* data, size_t length, uint16_t bit_depth) {
    std::vector<float> samples;
    
    switch (bit_depth) {
        case 8: {
            const uint8_t* input = static_cast<const uint8_t*>(data);
            samples.reserve(length);
            for (size_t i = 0; i < length; ++i) {
                samples.push_back((input[i] - 128) / 128.0f);
            }
            break;
        }
        case 16: {
            const int16_t* input = static_cast<const int16_t*>(data);
            size_t sample_count = length / 2;
            samples.reserve(sample_count);
            for (size_t i = 0; i < sample_count; ++i) {
                samples.push_back(input[i] / 32768.0f);
            }
            break;
        }
        case 32: {
            const float* input = static_cast<const float*>(data);
            size_t sample_count = length / 4;
            samples.assign(input, input + sample_count);
            break;
        }
    }
    
    return samples;
}

// HunterAudioPatterns Implementation
const float HunterAudioPatterns::PATTERN_MATCH_THRESHOLD = 0.8f;

std::vector<HunterAudioPatterns::SoundPattern> HunterAudioPatterns::getFightingSoundPatterns() {
    std::vector<SoundPattern> patterns;
    
    // Sword swing pattern
    SoundPattern sword_swing;
    sword_swing.name = "sword_swing";
    sword_swing.duration_ms = 500.0f;
    sword_swing.expected_volume = 0.7f;
    sword_swing.expected_channel = 2; // Effects channel
    // ... frequency signature would be populated from analysis ...
    patterns.push_back(sword_swing);
    
    // Enemy hit pattern
    SoundPattern enemy_hit;
    enemy_hit.name = "enemy_hit";
    enemy_hit.duration_ms = 200.0f;
    enemy_hit.expected_volume = 0.6f;
    enemy_hit.expected_channel = 2;
    patterns.push_back(enemy_hit);
    
    return patterns;
}

std::vector<HunterAudioPatterns::SoundPattern> HunterAudioPatterns::getMenuSoundPatterns() {
    std::vector<SoundPattern> patterns;
    
    // Menu selection sound
    SoundPattern menu_select;
    menu_select.name = "menu_select";
    menu_select.duration_ms = 100.0f;
    menu_select.expected_volume = 0.5f;
    menu_select.expected_channel = 1; // UI channel
    patterns.push_back(menu_select);
    
    return patterns;
}

std::vector<HunterAudioPatterns::SoundPattern> HunterAudioPatterns::getVoiceoverPatterns() {
    std::vector<SoundPattern> patterns;
    
    // Character dialogue
    SoundPattern dialogue;
    dialogue.name = "character_dialogue";
    dialogue.duration_ms = 2000.0f;
    dialogue.expected_volume = 0.8f;
    dialogue.expected_channel = 0; // Voice channel
    patterns.push_back(dialogue);
    
    return patterns;
}

bool HunterAudioPatterns::detectPattern(const SoundPattern& pattern,
                                       const std::vector<FrequencyBin>& current_spectrum) {
    // Implementation would compare current spectrum with pattern's frequency signature
    // Return true if match confidence > PATTERN_MATCH_THRESHOLD
    return false; // Placeholder
}

// DirectSoundMonitor Implementation
void DirectSoundMonitor::registerBuffer(uint32_t buffer_id, const DSBufferInfo& info) {
    std::lock_guard<std::mutex> lock(buffer_mutex_);
    buffers_[buffer_id] = info;
}

void DirectSoundMonitor::updateBufferState(uint32_t buffer_id, bool playing, float volume) {
    std::lock_guard<std::mutex> lock(buffer_mutex_);
    auto it = buffers_.find(buffer_id);
    if (it != buffers_.end()) {
        it->second.is_playing = playing;
        it->second.volume = volume;
    }
}

void DirectSoundMonitor::logAPICall(const std::string& function_name, 
                                   const std::vector<std::string>& params) {
    std::ostringstream oss;
    oss << function_name << "(";
    for (size_t i = 0; i < params.size(); ++i) {
        oss << params[i];
        if (i < params.size() - 1) oss << ", ";
    }
    oss << ")";
    
    api_call_log_.push_back(oss.str());
    
    // Keep only last 1000 API calls
    if (api_call_log_.size() > 1000) {
        api_call_log_.erase(api_call_log_.begin());
    }
}

std::vector<DirectSoundMonitor::DSBufferInfo> DirectSoundMonitor::getActiveBuffers() const {
    std::lock_guard<std::mutex> lock(buffer_mutex_);
    std::vector<DSBufferInfo> active;
    
    for (const auto& pair : buffers_) {
        if (pair.second.is_playing) {
            active.push_back(pair.second);
        }
    }
    
    return active;
}

std::vector<DirectSoundMonitor::DSBufferInfo> DirectSoundMonitor::getMissingExpectedBuffers() const {
    // This would implement logic to detect expected but missing audio buffers
    // based on Hunter: The Reckoning's typical audio setup
    return {};
}

} // namespace AudioDiagnostics