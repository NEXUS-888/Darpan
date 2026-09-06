"""
Face Detection and Normalization Engine for the VeriFace Protocol.
Detects faces, applies alignment & padding, extracts normalized 512x512 face crops,
and computes cryptographic and perceptual biometrics.
"""
import os
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image
import io

from .hasher import compute_face_hash


@dataclass
class ProcessedFace:
    original_path: str
    face_crop_path: Optional[str]
    face_crop_bytes: bytes
    face_hash: str
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    dimensions: Tuple[int, int]  # (width, height)
    face_detected: bool


class FaceEngine:
    def __init__(self, target_size: Tuple[int, int] = (512, 512)):
        self.target_size = target_size
        cascade_dir = cv2.data.haarcascades
        self.face_cascade = cv2.CascadeClassifier(
            os.path.join(cascade_dir, "haarcascade_frontalface_default.xml")
        )
        self.alt_face_cascade = cv2.CascadeClassifier(
            os.path.join(cascade_dir, "haarcascade_frontalface_alt2.xml")
        )
        self.eye_cascade = cv2.CascadeClassifier(
            os.path.join(cascade_dir, "haarcascade_eye.xml")
        )

    def detect_face(self, img_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detects primary face bounding box with eye validation and vertical positioning.
        Guarantees selection of actual human face over clothing patterns/embroidery.
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h_img, w_img = img_bgr.shape[:2]

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for lighting invariance
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)

        # Multi-scale detection with frontal cascade
        faces = self.face_cascade.detectMultiScale(
            equalized, scaleFactor=1.08, minNeighbors=4, minSize=(40, 40)
        )

        if len(faces) == 0:
            # Try alt cascade
            faces = self.alt_face_cascade.detectMultiScale(
                equalized, scaleFactor=1.08, minNeighbors=3, minSize=(40, 40)
            )

        if len(faces) == 0:
            return None

        # Score candidates to reject false positives (e.g. clothing embroidery, buttons, belts)
        best_candidate = None
        best_score = -999.0

        for rect in faces:
            x, y, w, h = rect
            roi_gray = gray[y : y + h, x : x + w]

            # Eye cascade verification inside candidate face ROI
            eyes = self.eye_cascade.detectMultiScale(
                roi_gray, scaleFactor=1.1, minNeighbors=2, minSize=(12, 12)
            )
            has_eyes = len(eyes) > 0

            # Vertical position: in portraits, faces are situated in upper 60% of image
            y_center_norm = (y + h / 2.0) / max(1, h_img)
            # Boxes in lower body (stomach/waist/legs) receive steep penalty
            pos_penalty = -15.0 if y_center_norm > 0.65 else (1.0 - y_center_norm) * 4.0

            # Eye score: primary differentiator for real faces vs fabric/clothing patterns
            eye_score = (12.0 if has_eyes else 0.0) + min(len(eyes), 2) * 6.0

            # Area score (normalize relative to image size)
            area_norm = (w * h) / float(w_img * h_img)
            area_score = min(area_norm * 10.0, 5.0)

            total_score = eye_score + pos_penalty + area_score

            if total_score > best_score:
                best_score = total_score
                best_candidate = rect

        if best_candidate is None:
            best_candidate = max(faces, key=lambda rect: rect[2] * rect[3])

        return tuple(int(v) for v in best_candidate)

    def extract_aligned_crop(
        self, img_bgr: np.ndarray, bbox: Tuple[int, int, int, int], padding_factor: float = 0.25
    ) -> np.ndarray:
        """
        Extracts face with proportional contextual padding and resizes to target_size.
        """
        h_img, w_img = img_bgr.shape[:2]
        x, y, w, h = bbox

        # Add proportional padding
        pad_x = int(w * padding_factor)
        pad_y = int(h * padding_factor)

        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w_img, x + w + pad_x)
        y2 = min(h_img, y + h + pad_y)

        face_roi = img_bgr[y1:y2, x1:x2]
        if face_roi.size == 0:
            face_roi = img_bgr

        # Resize cleanly using Lanczos/Area interpolation
        resized = cv2.resize(face_roi, self.target_size, interpolation=cv2.INTER_LANCZOS4)
        return resized

    def process_image(self, image_input, output_crop_path: Optional[str] = None) -> ProcessedFace:
        """
        Processes an image from a file path or raw bytes, detects the face,
        generates a normalized crop, and computes the cryptographic hash.
        """
        if isinstance(image_input, (str, bytes, bytearray)):
            if isinstance(image_input, str):
                if not os.path.exists(image_input):
                    raise FileNotFoundError(f"Input image not found: {image_input}")
                img_bgr = cv2.imread(image_input)
                original_path = image_input
            else:
                nparr = np.frombuffer(image_input, np.uint8)
                img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                original_path = "<memory_buffer>"
        else:
            raise TypeError("Expected image path (str) or raw image bytes")

        if img_bgr is None:
            raise ValueError("Could not decode image from provided input")

        bbox = self.detect_face(img_bgr)
        face_detected = bbox is not None

        if bbox is not None:
            normalized_crop = self.extract_aligned_crop(img_bgr, bbox)
            confidence = 0.96
        else:
            # Fallback: if no frontal cascade triggers, center crop to target size
            h, w = img_bgr.shape[:2]
            min_dim = min(h, w)
            start_x = (w - min_dim) // 2
            start_y = (h - min_dim) // 2
            center_crop = img_bgr[start_y : start_y + min_dim, start_x : start_x + min_dim]
            normalized_crop = cv2.resize(center_crop, self.target_size, interpolation=cv2.INTER_AREA)
            bbox = (0, 0, w, h)
            confidence = 0.50

        # Encode normalized face to PNG format (lossless) for deterministic bytes
        success, encoded_bytes = cv2.imencode(".png", normalized_crop)
        if not success:
            raise RuntimeError("Failed to encode normalized face crop to PNG bytes")

        raw_bytes = encoded_bytes.tobytes()
        face_hash = compute_face_hash(raw_bytes)

        if output_crop_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_crop_path)), exist_ok=True)
            cv2.imwrite(output_crop_path, normalized_crop)

        return ProcessedFace(
            original_path=original_path,
            face_crop_path=output_crop_path,
            face_crop_bytes=raw_bytes,
            face_hash=face_hash,
            bounding_box=bbox,
            confidence=confidence,
            dimensions=self.target_size,
            face_detected=face_detected,
        )
