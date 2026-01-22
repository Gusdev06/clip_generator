"""
Face detection and tracking module using MediaPipe
Enhanced version with precise face landmarks for TikTok-style clips
"""
import cv2
import numpy as np
from collections import deque
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config
import os
import urllib.request
from pathlib import Path


class FaceTracker:
    # Model URLs from MediaPipe
    FACE_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    FACE_DETECTOR_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"

    def __init__(self):
        """Initialize face detection using MediaPipe Face Detection + Face Mesh"""
        # Download models if needed
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)

        landmarker_model_path = models_dir / "face_landmarker.task"

        if not landmarker_model_path.exists():
            print(f"Downloading face landmarker model...")
            urllib.request.urlretrieve(self.FACE_LANDMARKER_MODEL_URL, landmarker_model_path)
            print(f"✓ Model downloaded to {landmarker_model_path}")

        # Initialize landmarker
        self._init_landmarker()

        # For smoothing face positions
        self.position_history = deque(maxlen=config.SMOOTHING_WINDOW)
        self.landmark_history = deque(maxlen=config.SMOOTHING_WINDOW)

        # Key landmark indices for face orientation
        self.FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                          397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                          172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.NOSE_TIP = 1
        self.CHIN = 152
        self.LEFT_CHEEK = 234
        self.RIGHT_CHEEK = 454

    def detect_face(self, frame, timestamp_ms=0):
        """
        Detect face with precise landmarks in a single frame

        Args:
            frame: OpenCV frame (BGR format)
            timestamp_ms: Video timestamp in milliseconds

        Returns:
            dict: Face bounding box info with landmarks or None if no face detected
                {
                    'x_center': normalized x coordinate (0-1),
                    'y_center': normalized y coordinate (0-1),
                    'width': normalized width (0-1),
                    'height': normalized height (0-1),
                    'confidence': detection confidence,
                    'landmarks': face mesh landmarks,
                    'eyes_center': center point between eyes,
                    'face_angle': rotation angle of face
                }
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = frame.shape[:2]

        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Detect face landmarks (this includes detection + landmarks)
        landmarker_result = self.face_landmarker.detect_for_video(mp_image, timestamp_ms)

        if not landmarker_result.face_landmarks:
            return None

        # Get the first face
        face_landmarks = landmarker_result.face_landmarks[0]

        # Extract key landmarks as numpy array
        landmarks_array = np.array([(lm.x, lm.y, lm.z) for lm in face_landmarks])

        # Calculate eyes center for better framing
        left_eye_points = landmarks_array[self.LEFT_EYE]
        right_eye_points = landmarks_array[self.RIGHT_EYE]
        left_eye_center = np.mean(left_eye_points[:, :2], axis=0)
        right_eye_center = np.mean(right_eye_points[:, :2], axis=0)
        eyes_center = (left_eye_center + right_eye_center) / 2

        # Calculate face angle (rotation) for better tracking
        eye_vector = right_eye_center - left_eye_center
        face_angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))

        # Get face oval for tight bounding
        face_oval_points = landmarks_array[self.FACE_OVAL][:, :2]

        # Calculate bounding box from landmarks
        x_coords = face_oval_points[:, 0]
        y_coords = face_oval_points[:, 1]

        bbox_x = np.min(x_coords)
        bbox_y = np.min(y_coords)
        bbox_w = np.max(x_coords) - bbox_x
        bbox_h = np.max(y_coords) - bbox_y

        landmarks_data = {
            'all_points': landmarks_array,
            'eyes_center': eyes_center,
            'face_oval': face_oval_points,
            'left_eye': left_eye_center,
            'right_eye': right_eye_center,
            'nose_tip': landmarks_array[self.NOSE_TIP][:2],
            'chin': landmarks_array[self.CHIN][:2]
        }

        # Return face data with enhanced information
        face_data = {
            'x_center': bbox_x + bbox_w / 2,
            'y_center': bbox_y + bbox_h / 2,
            'width': bbox_w,
            'height': bbox_h,
            'confidence': 1.0,  # New API doesn't provide confidence
            'landmarks': landmarks_data,
            'eyes_center': eyes_center,
            'face_angle': face_angle
        }

        return face_data

    def get_smoothed_position(self, face_data):
        """
        Apply advanced smoothing to face position to reduce jitter
        Uses exponential weighted average with landmark awareness

        Args:
            face_data: Face detection data from detect_face()

        Returns:
            dict: Smoothed face position data
        """
        if face_data is None:
            # If no face detected, use last known position
            if self.position_history:
                return self.position_history[-1]
            return None

        # Add to history
        self.position_history.append(face_data)

        if face_data['landmarks']:
            self.landmark_history.append(face_data['landmarks'])

        # Calculate weighted average (more recent = higher weight)
        if len(self.position_history) < 2:
            return face_data

        # Use exponential weighted average for smoother tracking
        weights = np.exp(np.linspace(-2, 0, len(self.position_history)))
        weights /= weights.sum()

        # Smooth basic position
        smoothed = {
            'x_center': sum(w * pos['x_center'] for w, pos in zip(weights, self.position_history)),
            'y_center': sum(w * pos['y_center'] for w, pos in zip(weights, self.position_history)),
            'width': sum(w * pos['width'] for w, pos in zip(weights, self.position_history)),
            'height': sum(w * pos['height'] for w, pos in zip(weights, self.position_history)),
            'confidence': face_data['confidence'],
            'face_angle': sum(w * pos['face_angle'] for w, pos in zip(weights, self.position_history)),
        }

        # Smooth landmarks if available
        if self.landmark_history and len(self.landmark_history) > 1:
            smoothed_eyes_center = np.average(
                [lm['eyes_center'] for lm in self.landmark_history],
                weights=weights[-len(self.landmark_history):],
                axis=0
            )
            smoothed['eyes_center'] = smoothed_eyes_center
            smoothed['landmarks'] = face_data['landmarks']  # Keep full landmarks for reference
        else:
            smoothed['eyes_center'] = face_data.get('eyes_center')
            smoothed['landmarks'] = face_data.get('landmarks')

        return smoothed

    def calculate_crop_box(self, face_data, frame_width, frame_height, target_aspect=9/16):
        """
        Calculate optimal crop box for 9:16 format centered on face
        Enhanced with landmark-based positioning for professional framing

        Args:
            face_data: Face detection data (normalized coordinates)
            frame_width: Original frame width in pixels
            frame_height: Original frame height in pixels
            target_aspect: Target aspect ratio (width/height)

        Returns:
            tuple: (x, y, width, height) in pixels for crop box
        """
        if face_data is None:
            # Default to center crop if no face
            crop_height = frame_height
            crop_width = int(crop_height * target_aspect)
            if crop_width > frame_width:
                crop_width = frame_width
                crop_height = int(crop_width / target_aspect)

            x = (frame_width - crop_width) // 2
            y = (frame_height - crop_height) // 2
            return (x, y, crop_width, crop_height)

        # Use eyes center for better framing if available
        if face_data.get('eyes_center') is not None:
            focus_x = face_data['eyes_center'][0]
            focus_y = face_data['eyes_center'][1]
        else:
            focus_x = face_data['x_center']
            focus_y = face_data['y_center']

        # Convert normalized coordinates to pixels
        face_x = int(focus_x * frame_width)
        face_y = int(focus_y * frame_height)
        face_w = int(face_data['width'] * frame_width * config.HORIZONTAL_MARGIN)
        face_h = int(face_data['height'] * frame_height * config.VERTICAL_MARGIN)

        # Calculate crop dimensions maintaining 9:16 aspect ratio
        crop_width = max(face_w, int(face_h * target_aspect))
        crop_height = int(crop_width / target_aspect)

        # Ensure minimum crop size
        if crop_width < config.MIN_CROP_WIDTH:
            crop_width = config.MIN_CROP_WIDTH
            crop_height = int(crop_width / target_aspect)

        # Check maximum zoom
        max_crop_width = int(frame_width / config.MAX_ZOOM)
        if crop_width > max_crop_width:
            crop_width = max_crop_width
            crop_height = int(crop_width / target_aspect)

        # Position face at FACE_VERTICAL_POSITION (e.g., 0.35 = upper third)
        # Use eyes as reference point for more professional framing
        crop_x = face_x - crop_width // 2
        crop_y = int(face_y - crop_height * config.FACE_VERTICAL_POSITION)

        # Ensure crop box stays within frame bounds
        crop_x = max(0, min(crop_x, frame_width - crop_width))
        crop_y = max(0, min(crop_y, frame_height - crop_height))

        # Ensure crop dimensions don't exceed frame
        if crop_x + crop_width > frame_width:
            crop_width = frame_width - crop_x
            crop_height = int(crop_width / target_aspect)

        if crop_y + crop_height > frame_height:
            crop_height = frame_height - crop_y
            crop_width = int(crop_height * target_aspect)

        return (crop_x, crop_y, crop_width, crop_height)

    def draw_debug_info(self, frame, face_data, crop_box):
        """
        Draw debug information on frame for visualization

        Args:
            frame: OpenCV frame to draw on
            face_data: Face detection data
            crop_box: Crop box tuple (x, y, w, h)

        Returns:
            frame with debug visualization
        """
        if face_data is None:
            return frame

        h, w = frame.shape[:2]
        debug_frame = frame.copy()

        # Draw crop box
        x, y, cw, ch = crop_box
        cv2.rectangle(debug_frame, (x, y), (x + cw, y + ch), (0, 255, 0), 3)

        # Draw landmarks if available
        if face_data.get('landmarks'):
            landmarks = face_data['landmarks']

            # Draw eyes center
            eyes_center = (int(landmarks['eyes_center'][0] * w),
                          int(landmarks['eyes_center'][1] * h))
            cv2.circle(debug_frame, eyes_center, 8, (0, 0, 255), -1)

            # Draw face oval
            for point in landmarks['face_oval']:
                px, py = int(point[0] * w), int(point[1] * h)
                cv2.circle(debug_frame, (px, py), 2, (255, 255, 0), -1)

            # Draw eye centers
            left_eye = (int(landmarks['left_eye'][0] * w),
                       int(landmarks['left_eye'][1] * h))
            right_eye = (int(landmarks['right_eye'][0] * w),
                        int(landmarks['right_eye'][1] * h))
            cv2.circle(debug_frame, left_eye, 4, (255, 0, 0), -1)
            cv2.circle(debug_frame, right_eye, 4, (255, 0, 0), -1)

            # Draw nose tip
            nose = (int(landmarks['nose_tip'][0] * w),
                   int(landmarks['nose_tip'][1] * h))
            cv2.circle(debug_frame, nose, 4, (0, 255, 255), -1)

        # Draw confidence and angle
        conf_text = f"Conf: {face_data['confidence']:.2f}"
        angle_text = f"Angle: {face_data['face_angle']:.1f}°"
        cv2.putText(debug_frame, conf_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_frame, angle_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return debug_frame

    def _init_landmarker(self):
        """Initialize or re-initialize the MediaPipe Face Landmarker"""
        if hasattr(self, 'face_landmarker') and self.face_landmarker:
            self.face_landmarker.close()

        # Initialize MediaPipe with new API
        models_dir = Path("models")
        landmarker_model_path = models_dir / "face_landmarker.task"
        
        base_options_landmarks = python.BaseOptions(model_asset_path=str(landmarker_model_path))

        # Face Landmarker options (combines detection + landmarks)
        landmarker_options = vision.FaceLandmarkerOptions(
            base_options=base_options_landmarks,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
        )

        # Create landmarker
        self.face_landmarker = vision.FaceLandmarker.create_from_options(landmarker_options)

    def reset(self):
        """Reset tracking history and re-initialize model for new video"""
        self.position_history.clear()
        self.landmark_history.clear()
        
        # Re-initialize landmarker to reset internal timestamp state
        self._init_landmarker()

    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'face_landmarker') and self.face_landmarker:
            self.face_landmarker.close()


if __name__ == "__main__":
    # Test the face tracker with webcam
    tracker = FaceTracker()
    cap = cv2.VideoCapture(0)

    print("Testing enhanced face tracker with MediaPipe landmarks")
    print("Features:")
    print("  - Precise face detection with 468 landmarks")
    print("  - Eye-centered framing")
    print("  - Face angle detection")
    print("  - Smooth tracking")
    print("\nPress 'q' to quit, 'd' to toggle debug view")

    debug_mode = True

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect and track face
        face_data = tracker.detect_face(frame)
        smoothed_face = tracker.get_smoothed_position(face_data)

        if smoothed_face:
            # Calculate crop box
            h, w = frame.shape[:2]
            crop_box = tracker.calculate_crop_box(smoothed_face, w, h)

            if debug_mode:
                # Show debug visualization
                display_frame = tracker.draw_debug_info(frame, smoothed_face, crop_box)
            else:
                # Show just the crop box
                display_frame = frame.copy()
                x, y, cw, ch = crop_box
                cv2.rectangle(display_frame, (x, y), (x + cw, y + ch), (0, 255, 0), 2)
        else:
            display_frame = frame

        cv2.imshow('Enhanced Face Tracking Test', display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            debug_mode = not debug_mode
            print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()
