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


def test_face_engine_extract_embedding(sample_image_path):
    engine = FaceEngine()
    emb = engine.extract_embedding(sample_image_path)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (512,)
    # Embedding vector should be unit-normalized
    norm = np.linalg.norm(emb)
    assert np.isclose(norm, 1.0, atol=1e-3)


def test_face_engine_similarity_self_match(sample_image_path):
    engine = FaceEngine()
    sim = engine.compute_similarity(sample_image_path, sample_image_path)
    assert sim.score >= 0.98
    assert sim.verified is True
    assert sim.distance <= 0.02
    assert sim.metric == "cosine"
    assert "ArcFace" in sim.model_used or "arcface" in sim.model_used.lower()

    # Dictionary representation
    d = sim.to_dict()
    assert "score" in d
    assert "verified" in d
    assert d["verified"] is True


def test_face_engine_similarity_discrimination(sample_image_path, tmp_path):
    engine = FaceEngine()

    # Create slightly blurred version of the face
    orig = cv2.imread(sample_image_path)
    blurred = cv2.GaussianBlur(orig, (7, 7), 1.5)
    blurred_path = str(tmp_path / "blurred.jpg")
    cv2.imwrite(blurred_path, blurred)

    # Create random noise image
    noise = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
    noise_path = str(tmp_path / "noise.jpg")
    cv2.imwrite(noise_path, noise)

    sim_blurred = engine.compute_similarity(sample_image_path, blurred_path)
    sim_noise = engine.compute_similarity(sample_image_path, noise_path)

    # Blurred variant should have significantly higher similarity than random noise
    assert sim_blurred.score > 0.85
    assert sim_blurred.verified is True
    assert sim_noise.score < 0.40
    assert sim_noise.verified is False
    assert sim_blurred.score > sim_noise.score + 0.40


def test_face_engine_input_types(sample_image_path):
    engine = FaceEngine()
    # Test passing ProcessedFace object
    processed = engine.process_image(sample_image_path)
    sim_from_processed = engine.compute_similarity(processed, sample_image_path)
    assert sim_from_processed.score >= 0.95

    # Test passing raw bytes
    with open(sample_image_path, "rb") as f:
        img_bytes = f.read()
    sim_bytes = engine.compute_similarity(img_bytes, sample_image_path)
    assert sim_bytes.score >= 0.95

    # Test passing raw numpy ndarray
    img_arr = cv2.imread(sample_image_path)
    sim_arr = engine.compute_similarity(img_arr, sample_image_path)
    assert sim_arr.score >= 0.95


def test_face_engine_invalid_input_graceful_handling():
    engine = FaceEngine()
    # Nonexistent path or invalid URL should not raise unhandled exception
    sim = engine.compute_similarity("nonexistent_path_12345.jpg", "invalid_path_67890.jpg")
    assert sim.score == 0.0
    assert sim.verified is False
    assert "error" in sim.details
