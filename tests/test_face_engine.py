"""
Unit tests for the FaceEngine module.
"""
import os
import pytest
import numpy as np
import cv2

from src.face_engine import FaceEngine


@pytest.fixture
def sample_image_path():
    path = os.path.join(os.path.dirname(__file__), "..", "samples", "demo_face.jpg")
    if not os.path.exists(path):
        pytest.skip("Sample demo_face.jpg not found")
    return path


def test_face_engine_initialization():
    engine = FaceEngine()
    assert engine.target_size == (512, 512)
    assert engine.face_cascade is not None


def test_face_engine_processing(sample_image_path, tmp_path):
    engine = FaceEngine()
    crop_out = str(tmp_path / "crop.png")
    processed = engine.process_image(sample_image_path, output_crop_path=crop_out)

    assert processed.face_detected is True
    assert processed.confidence > 0.8
    assert processed.face_hash.startswith("0x")
    assert len(processed.face_hash) == 66
    assert os.path.exists(crop_out)

    # Check output crop dimensions
    img = cv2.imread(crop_out)
    assert img.shape == (512, 512, 3)


def test_face_engine_synthetic_fallback(tmp_path):
    # Blank canvas with no face
    blank = np.zeros((300, 300, 3), dtype=np.uint8)
    blank_path = str(tmp_path / "blank.png")
    cv2.imwrite(blank_path, blank)

    engine = FaceEngine()
    processed = engine.process_image(blank_path)
    # Should gracefully fallback to center crop without crashing
    assert processed.face_hash.startswith("0x")
    assert processed.dimensions == (512, 512)
