"""
Lip sync detection module
Correlates mouth movement from face landmarks with audio signal
to identify which person on screen is speaking
"""
import numpy as np
from scipy import signal
from collections import deque
import cv2


class LipSyncDetector:
    """
    Detects correlation between lip movement and audio
    to identify who is speaking in multi-person videos
    """

    def __init__(self, window_size=10):
        """
        Initialize lip sync detector

        Args:
            window_size: Number of frames to use for correlation analysis
        """
        self.window_size = window_size
        self.mouth_history = deque(maxlen=window_size)
        self.audio_history = deque(maxlen=window_size)

        # Mouth landmark indices (from MediaPipe Face Mesh)
        # Outer lips
        self.UPPER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]
        self.LOWER_LIP = [146, 91, 181, 84, 17, 314, 405, 321, 375, 291]

        # Inner lips (for mouth opening detection)
        self.INNER_UPPER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308]
        self.INNER_LOWER = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]

        # For vertical mouth opening
        self.MOUTH_TOP = 13  # Upper inner lip center
        self.MOUTH_BOTTOM = 14  # Lower inner lip center

    def calculate_mouth_opening(self, landmarks):
        """
        Calculate mouth opening ratio from face landmarks

        Args:
            landmarks: Face landmarks from MediaPipe (normalized 0-1)

        Returns:
            float: Mouth opening ratio (0 = closed, higher = more open)
        """
        if landmarks is None:
            return 0.0

        try:
            # Get landmarks array
            if isinstance(landmarks, dict) and 'all_points' in landmarks:
                points = landmarks['all_points']
            else:
                points = landmarks

            # Calculate vertical mouth opening
            top = points[self.MOUTH_TOP][:2]
            bottom = points[self.MOUTH_BOTTOM][:2]
            vertical_distance = np.linalg.norm(top - bottom)

            # Calculate mouth width for normalization
            left = points[61][:2]  # Left mouth corner
            right = points[291][:2]  # Right mouth corner
            mouth_width = np.linalg.norm(left - right)

            # Normalize by mouth width to handle different face sizes
            if mouth_width > 0:
                mouth_ratio = vertical_distance / mouth_width
            else:
                mouth_ratio = 0.0

            return mouth_ratio

        except (IndexError, KeyError, TypeError):
            return 0.0

    def calculate_mouth_area(self, landmarks):
        """
        Calculate approximate mouth area using convex hull

        Args:
            landmarks: Face landmarks

        Returns:
            float: Mouth area (normalized)
        """
        if landmarks is None:
            return 0.0

        try:
            if isinstance(landmarks, dict) and 'all_points' in landmarks:
                points = landmarks['all_points']
            else:
                points = landmarks

            # Get outer lip points
            outer_lip_points = np.array([points[i][:2] for i in self.UPPER_LIP + self.LOWER_LIP])

            # Calculate convex hull area
            from scipy.spatial import ConvexHull
            if len(outer_lip_points) >= 3:
                hull = ConvexHull(outer_lip_points)
                area = hull.volume  # In 2D, volume = area
                return area
            else:
                return 0.0

        except:
            return 0.0

    def calculate_lip_movement(self, landmarks, prev_landmarks):
        """
        Calculate how much the lips moved between frames

        Args:
            landmarks: Current frame landmarks
            prev_landmarks: Previous frame landmarks

        Returns:
            float: Magnitude of lip movement
        """
        if landmarks is None or prev_landmarks is None:
            return 0.0

        try:
            if isinstance(landmarks, dict) and 'all_points' in landmarks:
                current_points = landmarks['all_points']
                prev_points = prev_landmarks['all_points']
            else:
                current_points = landmarks
                prev_points = prev_landmarks

            # Get lip points
            lip_indices = self.UPPER_LIP + self.LOWER_LIP

            # Calculate movement for each lip point
            movements = []
            for idx in lip_indices:
                curr = current_points[idx][:2]
                prev = prev_points[idx][:2]
                movement = np.linalg.norm(curr - prev)
                movements.append(movement)

            # Return average movement
            return np.mean(movements) if movements else 0.0

        except:
            return 0.0

    def correlate_with_audio(self, mouth_features, audio_energy):
        """
        Calculate correlation between mouth movement and audio energy

        Args:
            mouth_features: Array of mouth opening/movement values
            audio_energy: Array of audio energy values (same length)

        Returns:
            float: Correlation coefficient (-1 to 1)
        """
        if len(mouth_features) < 2 or len(audio_energy) < 2:
            return 0.0

        # Ensure same length
        min_len = min(len(mouth_features), len(audio_energy))
        mouth_features = mouth_features[:min_len]
        audio_energy = audio_energy[:min_len]

        # Normalize
        mouth_norm = (mouth_features - np.mean(mouth_features))
        audio_norm = (audio_energy - np.mean(audio_energy))

        # Avoid division by zero
        mouth_std = np.std(mouth_norm)
        audio_std = np.std(audio_norm)

        if mouth_std < 1e-10 or audio_std < 1e-10:
            return 0.0

        mouth_norm /= mouth_std
        audio_norm /= audio_std

        # Calculate cross-correlation
        correlation = signal.correlate(mouth_norm, audio_norm, mode='valid')

        # Return max correlation (accounting for small delays)
        if len(correlation) > 0:
            return np.max(np.abs(correlation)) / min_len
        else:
            return 0.0

    def is_speaking(self, face_landmarks, audio_energy, threshold=0.3):
        """
        Determine if a person is speaking based on lip-audio sync

        Args:
            face_landmarks: Current face landmarks
            audio_energy: Current audio energy
            threshold: Correlation threshold (0-1)

        Returns:
            dict: {
                'is_speaking': bool,
                'confidence': float,
                'mouth_opening': float,
                'correlation': float
            }
        """
        # Calculate mouth opening
        mouth_opening = self.calculate_mouth_opening(face_landmarks)

        # Add to history
        self.mouth_history.append(mouth_opening)
        self.audio_history.append(audio_energy)

        # Need enough history for correlation
        if len(self.mouth_history) < self.window_size // 2:
            return {
                'is_speaking': False,
                'confidence': 0.0,
                'mouth_opening': mouth_opening,
                'correlation': 0.0
            }

        # Calculate correlation
        mouth_array = np.array(self.mouth_history)
        audio_array = np.array(self.audio_history)

        correlation = self.correlate_with_audio(mouth_array, audio_array)

        # Determine if speaking
        # Consider both mouth opening and correlation
        mouth_active = mouth_opening > 0.15  # Mouth is open
        audio_active = audio_energy > np.mean(audio_array) * 0.5  # Audio present
        correlated = correlation > threshold  # Lip-audio sync

        is_speaking = mouth_active and audio_active and correlated
        confidence = correlation if is_speaking else 0.0

        return {
            'is_speaking': is_speaking,
            'confidence': confidence,
            'mouth_opening': mouth_opening,
            'correlation': correlation
        }

    def track_multiple_speakers(self, faces_landmarks, audio_energy):
        """
        Track multiple faces and determine which one is speaking

        Args:
            faces_landmarks: List of face landmarks for each detected face
            audio_energy: Current audio energy

        Returns:
            list: List of dicts with speaking status for each face
        """
        results = []

        for i, landmarks in enumerate(faces_landmarks):
            speaking_info = self.is_speaking(landmarks, audio_energy)
            speaking_info['face_id'] = i
            results.append(speaking_info)

        # Sort by confidence (most likely speaker first)
        results.sort(key=lambda x: x['confidence'], reverse=True)

        return results

    def reset(self):
        """Reset tracking history"""
        self.mouth_history.clear()
        self.audio_history.clear()


class MultiPersonLipSync:
    """
    Manages lip sync detection for multiple people in frame
    """

    def __init__(self, num_faces=4):
        """
        Initialize multi-person lip sync

        Args:
            num_faces: Maximum number of faces to track
        """
        self.detectors = [LipSyncDetector() for _ in range(num_faces)]
        self.num_faces = num_faces

    def analyze_frame(self, faces_landmarks, audio_energy):
        """
        Analyze which face is speaking in current frame

        Args:
            faces_landmarks: List of face landmarks
            audio_energy: Current audio energy

        Returns:
            dict: {
                'active_speaker_id': int or None,
                'speaker_scores': list of (face_id, score) tuples
            }
        """
        if not faces_landmarks:
            return {
                'active_speaker_id': None,
                'speaker_scores': []
            }

        scores = []

        for i, landmarks in enumerate(faces_landmarks[:self.num_faces]):
            if i < len(self.detectors):
                result = self.detectors[i].is_speaking(landmarks, audio_energy)
                scores.append((i, result['confidence']))

        # Sort by confidence
        scores.sort(key=lambda x: x[1], reverse=True)

        # Active speaker is the one with highest confidence
        active_speaker = scores[0][0] if scores and scores[0][1] > 0.2 else None

        return {
            'active_speaker_id': active_speaker,
            'speaker_scores': scores
        }

    def reset(self):
        """Reset all detectors"""
        for detector in self.detectors:
            detector.reset()


if __name__ == "__main__":
    print("Lip Sync Detector Test")
    print("=" * 50)
    print("\nThis module detects correlation between lip movement and audio")
    print("to identify who is speaking in multi-person videos.")
    print("\nKey features:")
    print("  - Mouth opening detection from 468 facial landmarks")
    print("  - Lip-audio correlation analysis")
    print("  - Multi-speaker tracking")
    print("  - Real-time speaking confidence scores")
    print("\nIntegrate with face_tracker.py and audio_analyzer.py for complete system")
