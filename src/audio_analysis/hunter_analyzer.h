#pragma once

#include <vector>
#include <string>
#include <memory>

namespace HunterAnalysis {

struct AudioSample {
    std::vector<float> data;
    uint32_t sample_rate;
    uint16_t channels;
    std::string source_info;
};

struct AnalysisResult {
    std::vector<int> missing_pattern_indices;
    std::vector<int> missing_clusters;
    float overall_similarity;
    std::string recommendations;
    bool analysis_successful;
};

class HunterAudioAnalyzer {
public:
    HunterAudioAnalyzer();
    ~HunterAudioAnalyzer();
    
    // Load audio samples
    bool loadReferenceAudio(const std::string& filepath);
    bool loadEmulatedAudio(const std::string& filepath);
    bool loadAudioFromMemory(const std::vector<float>& samples, uint32_t sample_rate, 
                           bool is_reference = true);
    
    // Run analysis
    AnalysisResult analyzeAudioDifferences();
    
    // Export results
    bool exportAnalysisResults(const std::string& filepath);
    bool exportMissingPatterns(const std::string& filepath);
    
    // Configuration
    void setAnalysisParameters(float similarity_threshold = 0.7f, int num_clusters = 10);
    void enableVisualization(bool enable);
    
    // Integration helpers for xemu
    static std::shared_ptr<HunterAudioAnalyzer> createForXemuIntegration();
    void processXemuAudioFrame(const void* audio_data, size_t length, 
                              uint32_t sample_rate, uint16_t channels);
    
private:
    class Impl; // PIMPL idiom to hide Python integration details
    std::unique_ptr<Impl> pimpl_;
};

// Utility functions for xemu integration
namespace XemuIntegration {
    
    // Hook into xemu's audio pipeline
    bool installAudioHooks();
    void removeAudioHooks();
    
    // Audio capture callback type
    using AudioCaptureCallback = std::function<void(int channel, const void* data, 
                                                   size_t length, uint32_t sample_rate)>;
    
    // Register callback for audio monitoring
    void setAudioCaptureCallback(AudioCaptureCallback callback);
    
    // Start/stop audio analysis session
    void startAnalysisSession();
    void stopAnalysisSession();
    
    // Get current analysis results
    AnalysisResult getCurrentAnalysisResults();
}

} // namespace HunterAnalysis