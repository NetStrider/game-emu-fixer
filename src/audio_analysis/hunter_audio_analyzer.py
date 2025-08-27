#!/usr/bin/env python3
"""
Hunter: The Reckoning Audio Analysis Tool

This tool uses machine learning to analyze audio patterns and identify
missing sound effects in the emulated version compared to reference recordings.
"""

import numpy as np
import librosa
import soundfile as sf
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import json
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class AudioFeatureExtractor:
    """Extract various audio features for analysis"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        
    def extract_mfcc(self, audio: np.ndarray, n_mfcc: int = 13) -> np.ndarray:
        """Extract MFCC features"""
        return librosa.feature.mfcc(
            y=audio, sr=self.sample_rate, n_mfcc=n_mfcc, hop_length=self.hop_length
        )
    
    def extract_spectral_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract spectral features"""
        features = {}
        
        # Spectral centroid
        features['spectral_centroid'] = librosa.feature.spectral_centroid(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        
        # Spectral rolloff
        features['spectral_rolloff'] = librosa.feature.spectral_rolloff(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        
        # Spectral bandwidth
        features['spectral_bandwidth'] = librosa.feature.spectral_bandwidth(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        
        # Zero crossing rate
        features['zero_crossing_rate'] = librosa.feature.zero_crossing_rate(
            audio, hop_length=self.hop_length
        )
        
        return features
    
    def extract_rhythm_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract rhythm-related features"""
        features = {}
        
        # Tempo and beat tracking
        tempo, beats = librosa.beat.beat_track(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        features['tempo'] = tempo
        features['beats'] = beats
        
        # Onset detection
        onset_frames = librosa.onset.onset_detect(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        features['onsets'] = librosa.times_like(onset_frames, sr=self.sample_rate)
        
        return features
    
    def extract_all_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract comprehensive feature set"""
        features = {}
        
        # MFCC features
        features['mfcc'] = self.extract_mfcc(audio)
        
        # Spectral features
        spectral_features = self.extract_spectral_features(audio)
        features.update(spectral_features)
        
        # Rhythm features
        rhythm_features = self.extract_rhythm_features(audio)
        features.update(rhythm_features)
        
        # Chroma features
        features['chroma'] = librosa.feature.chroma_stft(
            y=audio, sr=self.sample_rate, hop_length=self.hop_length
        )
        
        return features

class AudioPatternAnalyzer:
    """AI-driven audio pattern analysis for Hunter: The Reckoning"""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self.feature_extractor = AudioFeatureExtractor(sample_rate)
        self.scaler = StandardScaler()
        self.clusterer = KMeans(n_clusters=10, random_state=42)
        self.sound_patterns = {}
        
    def load_audio_file(self, filepath: str) -> Tuple[np.ndarray, int]:
        """Load audio file and resample if necessary"""
        audio, sr = librosa.load(filepath, sr=self.sample_rate)
        return audio, sr
    
    def segment_audio(self, audio: np.ndarray, segment_length: float = 2.0) -> List[np.ndarray]:
        """Segment audio into chunks for analysis"""
        segment_samples = int(segment_length * self.sample_rate)
        segments = []
        
        for i in range(0, len(audio) - segment_samples, segment_samples // 2):
            segment = audio[i:i + segment_samples]
            if len(segment) == segment_samples:
                segments.append(segment)
                
        return segments
    
    def analyze_missing_sounds(self, reference_audio: np.ndarray, 
                             emulated_audio: np.ndarray) -> Dict[str, any]:
        """Compare reference Xbox audio with emulated output"""
        
        # Segment both audio files
        ref_segments = self.segment_audio(reference_audio)
        emu_segments = self.segment_audio(emulated_audio)
        
        # Extract features for each segment
        ref_features = []
        for segment in ref_segments:
            features = self.feature_extractor.extract_all_features(segment)
            feature_vector = self._flatten_features(features)
            ref_features.append(feature_vector)
        
        emu_features = []
        for segment in emu_segments:
            features = self.feature_extractor.extract_all_features(segment)
            feature_vector = self._flatten_features(features)
            emu_features.append(feature_vector)
        
        if not ref_features or not emu_features:
            return {"error": "No valid segments found"}
        
        # Normalize features
        all_features = ref_features + emu_features
        all_features_scaled = self.scaler.fit_transform(all_features)
        
        ref_features_scaled = all_features_scaled[:len(ref_features)]
        emu_features_scaled = all_features_scaled[len(ref_features):]
        
        # Find missing patterns
        missing_patterns = self._find_missing_patterns(ref_features_scaled, emu_features_scaled)
        
        # Cluster analysis
        clusters = self._perform_cluster_analysis(ref_features_scaled, emu_features_scaled)
        
        return {
            "missing_patterns": missing_patterns,
            "cluster_analysis": clusters,
            "reference_segments": len(ref_segments),
            "emulated_segments": len(emu_segments),
            "similarity_matrix": self._compute_similarity_matrix(ref_features_scaled, emu_features_scaled)
        }
    
    def _flatten_features(self, features: Dict[str, np.ndarray]) -> np.ndarray:
        """Flatten all features into a single vector"""
        flattened = []
        
        for key, value in features.items():
            if key in ['tempo']:  # Scalar values
                flattened.extend([value])
            elif key in ['beats', 'onsets']:  # Variable length arrays
                # Take statistical measures
                if len(value) > 0:
                    flattened.extend([np.mean(value), np.std(value), len(value)])
                else:
                    flattened.extend([0, 0, 0])
            else:  # Feature matrices
                # Take statistical measures across time
                flattened.extend([
                    np.mean(value),
                    np.std(value),
                    np.max(value),
                    np.min(value)
                ])
        
        return np.array(flattened)
    
    def _find_missing_patterns(self, ref_features: np.ndarray, 
                              emu_features: np.ndarray, threshold: float = 0.7) -> List[int]:
        """Find reference patterns that don't have close matches in emulated audio"""
        missing = []
        
        for i, ref_pattern in enumerate(ref_features):
            similarities = cosine_similarity([ref_pattern], emu_features)[0]
            max_similarity = np.max(similarities)
            
            if max_similarity < threshold:
                missing.append(i)
        
        return missing
    
    def _perform_cluster_analysis(self, ref_features: np.ndarray, 
                                 emu_features: np.ndarray) -> Dict[str, any]:
        """Perform clustering analysis to identify sound categories"""
        
        # Fit clusterer on reference features
        ref_clusters = self.clusterer.fit_predict(ref_features)
        emu_clusters = self.clusterer.predict(emu_features)
        
        # Analyze cluster distributions
        ref_cluster_counts = np.bincount(ref_clusters)
        emu_cluster_counts = np.bincount(emu_clusters, minlength=len(ref_cluster_counts))
        
        missing_clusters = []
        for i, (ref_count, emu_count) in enumerate(zip(ref_cluster_counts, emu_cluster_counts)):
            if ref_count > 0 and emu_count == 0:
                missing_clusters.append(i)
        
        return {
            "missing_clusters": missing_clusters,
            "reference_distribution": ref_cluster_counts.tolist(),
            "emulated_distribution": emu_cluster_counts.tolist(),
            "cluster_centers": self.clusterer.cluster_centers_.tolist()
        }
    
    def _compute_similarity_matrix(self, ref_features: np.ndarray, 
                                  emu_features: np.ndarray) -> List[List[float]]:
        """Compute similarity matrix between reference and emulated segments"""
        similarity_matrix = cosine_similarity(ref_features, emu_features)
        return similarity_matrix.tolist()
    
    def identify_hunter_sound_types(self, audio: np.ndarray) -> Dict[str, List[Tuple[float, float]]]:
        """Identify specific Hunter: The Reckoning sound types"""
        
        # Define frequency ranges for different sound types
        sound_types = {
            "sword_hits": (1000, 4000),      # Metallic clanging sounds
            "footsteps": (200, 800),         # Low frequency impacts
            "voices": (85, 255),             # Human vocal range
            "ambient": (20, 200),            # Low frequency ambient
            "effects": (4000, 8000),         # High frequency effects
        }
        
        segments = self.segment_audio(audio, segment_length=1.0)
        detected_sounds = {sound_type: [] for sound_type in sound_types}
        
        for i, segment in enumerate(segments):
            timestamp = i * 0.5  # 50% overlap
            
            # Analyze frequency content
            stft = librosa.stft(segment)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=self.sample_rate)
            
            for sound_type, (low_freq, high_freq) in sound_types.items():
                # Find energy in frequency range
                freq_mask = (freqs >= low_freq) & (freqs <= high_freq)
                energy = np.sum(magnitude[freq_mask])
                
                # Threshold for detection
                if energy > np.percentile(magnitude, 90):
                    detected_sounds[sound_type].append((timestamp, timestamp + 1.0))
        
        return detected_sounds
    
    def generate_report(self, analysis_results: Dict[str, any], 
                       output_file: str = "hunter_audio_analysis.json"):
        """Generate comprehensive analysis report"""
        
        report = {
            "analysis_summary": analysis_results,
            "recommendations": self._generate_recommendations(analysis_results),
            "timestamp": np.datetime64('now').isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_recommendations(self, analysis_results: Dict[str, any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if "missing_patterns" in analysis_results:
            missing_count = len(analysis_results["missing_patterns"])
            if missing_count > 0:
                recommendations.append(
                    f"Found {missing_count} missing audio patterns. "
                    "Check DirectSound buffer management in emulator."
                )
        
        if "cluster_analysis" in analysis_results:
            missing_clusters = analysis_results["cluster_analysis"].get("missing_clusters", [])
            if missing_clusters:
                recommendations.append(
                    f"Missing sound categories: {missing_clusters}. "
                    "These may correspond to specific sound effect types."
                )
        
        # Add specific Hunter: The Reckoning recommendations
        recommendations.extend([
            "Check Xbox DirectSound 3D audio implementation",
            "Verify audio channel routing for fighting sounds",
            "Ensure proper audio buffer timing synchronization",
            "Implement missing frequency range processing (1-4kHz for combat sounds)"
        ])
        
        return recommendations
    
    def visualize_analysis(self, analysis_results: Dict[str, any], output_dir: str = "plots"):
        """Create visualizations of the analysis results"""
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # Plot similarity matrix
        if "similarity_matrix" in analysis_results:
            plt.figure(figsize=(10, 8))
            similarity_matrix = np.array(analysis_results["similarity_matrix"])
            sns.heatmap(similarity_matrix, cmap='viridis', cbar=True)
            plt.title("Reference vs Emulated Audio Similarity Matrix")
            plt.xlabel("Emulated Audio Segments")
            plt.ylabel("Reference Audio Segments")
            plt.savefig(f"{output_dir}/similarity_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
        
        # Plot cluster distribution
        if "cluster_analysis" in analysis_results:
            cluster_data = analysis_results["cluster_analysis"]
            ref_dist = cluster_data["reference_distribution"]
            emu_dist = cluster_data["emulated_distribution"]
            
            plt.figure(figsize=(12, 6))
            x = np.arange(len(ref_dist))
            width = 0.35
            
            plt.bar(x - width/2, ref_dist, width, label='Reference', alpha=0.8)
            plt.bar(x + width/2, emu_dist, width, label='Emulated', alpha=0.8)
            
            plt.xlabel('Sound Clusters')
            plt.ylabel('Frequency')
            plt.title('Sound Pattern Distribution: Reference vs Emulated')
            plt.legend()
            plt.savefig(f"{output_dir}/cluster_distribution.png", dpi=300, bbox_inches='tight')
            plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Hunter: The Reckoning audio issues using AI"
    )
    parser.add_argument("--reference", required=True, 
                       help="Reference audio file (original Xbox)")
    parser.add_argument("--emulated", required=True,
                       help="Emulated audio file (xemu output)")
    parser.add_argument("--output", default="hunter_analysis.json",
                       help="Output analysis file")
    parser.add_argument("--visualize", action="store_true",
                       help="Generate visualization plots")
    
    args = parser.parse_args()
    
    print("Hunter: The Reckoning Audio Analysis Tool")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = AudioPatternAnalyzer()
    
    # Load audio files
    print(f"Loading reference audio: {args.reference}")
    ref_audio, _ = analyzer.load_audio_file(args.reference)
    
    print(f"Loading emulated audio: {args.emulated}")
    emu_audio, _ = analyzer.load_audio_file(args.emulated)
    
    # Perform analysis
    print("Analyzing audio patterns...")
    results = analyzer.analyze_missing_sounds(ref_audio, emu_audio)
    
    # Identify Hunter-specific sound types
    print("Identifying game-specific sound types...")
    ref_sound_types = analyzer.identify_hunter_sound_types(ref_audio)
    emu_sound_types = analyzer.identify_hunter_sound_types(emu_audio)
    
    results["reference_sound_types"] = ref_sound_types
    results["emulated_sound_types"] = emu_sound_types
    
    # Generate report
    print(f"Generating analysis report: {args.output}")
    report = analyzer.generate_report(results, args.output)
    
    # Create visualizations if requested
    if args.visualize:
        print("Creating visualization plots...")
        analyzer.visualize_analysis(results)
    
    # Print summary
    print("\nAnalysis Summary:")
    print(f"- Reference segments: {results.get('reference_segments', 0)}")
    print(f"- Emulated segments: {results.get('emulated_segments', 0)}")
    print(f"- Missing patterns: {len(results.get('missing_patterns', []))}")
    print(f"- Missing sound clusters: {len(results.get('cluster_analysis', {}).get('missing_clusters', []))}")
    
    print("\nRecommendations:")
    for rec in report.get("recommendations", []):
        print(f"- {rec}")
    
    print(f"\nDetailed results saved to: {args.output}")

if __name__ == "__main__":
    main()