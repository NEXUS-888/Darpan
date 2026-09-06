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


def test_face_engine_insightface_attributes(sample_image_path):
    engine = FaceEngine(prefer_insightface=True)
    processed = engine.process_image(sample_image_path)
    assert hasattr(processed, "landmarks")
    assert hasattr(processed, "alignment_method")
    assert processed.face_detected is True
    if processed.landmarks is not None:
        assert len(processed.landmarks) == 5
        assert processed.alignment_method == "insightface_5point_affine"
    else:
        assert processed.alignment_method == "haar_box_crop"


def test_face_engine_rgba_conversion(tmp_path):
    # Create 4-channel BGRA image with alpha channel
    rgba = np.zeros((200, 200, 4), dtype=np.uint8)
    rgba[:, :, 0] = 255  # Blue
    rgba[:, :, 3] = 128  # Alpha
    rgba_path = str(tmp_path / "rgba_test.png")
    cv2.imwrite(rgba_path, rgba)

    engine = FaceEngine()
    loaded = engine._load_image(rgba_path)
    assert loaded is not None
    assert len(loaded.shape) == 3
    assert loaded.shape[2] == 3  # Normalized to 3-channel BGR


def test_face_engine_exif_orientation_handling(tmp_path):
    # Test that _load_image handles EXIF orientation transposition without crashing
    from PIL import Image
    im = Image.new("RGB", (100, 200), color="red")
    im_path = str(tmp_path / "portrait_exif.jpg")
    im.save(im_path, "JPEG")

    engine = FaceEngine()
    loaded = engine._load_image(im_path)
    assert loaded is not None
    assert loaded.shape == (200, 100, 3)


def test_face_engine_prefer_insightface_flag(sample_image_path):
    engine_no_insight = FaceEngine(prefer_insightface=False)
    processed = engine_no_insight.process_image(sample_image_path)
    assert processed.face_detected is True
    assert processed.alignment_method == "haar_box_crop"


def test_face_engine_cmyk_and_palette_handling(tmp_path):
    from PIL import Image
    # CMYK mode image
    cmyk_im = Image.new("CMYK", (80, 80), color=(100, 50, 0, 10))
    cmyk_path = str(tmp_path / "cmyk_test.jpg")
    cmyk_im.save(cmyk_path)

    engine = FaceEngine()
    loaded_cmyk = engine._load_image(cmyk_path)
    assert loaded_cmyk is not None
    assert loaded_cmyk.shape == (80, 80, 3)

    # Palette mode image (P)
    p_im = Image.new("P", (60, 60))
    p_path = str(tmp_path / "palette_test.png")
    p_im.save(p_path)
    loaded_p = engine._load_image(p_path)
    assert loaded_p is not None
    assert loaded_p.shape == (60, 60, 3)


def test_face_engine_align_face_5point_degenerate():
    engine = FaceEngine()
    dummy_img = np.zeros((200, 200, 3), dtype=np.uint8)
    # Degenerate points (all at same coordinate)
    kps_degenerate = np.array([[50.0, 50.0]] * 5, dtype=np.float32)
    aligned = engine.align_face_5point(dummy_img, kps_degenerate)
    assert aligned is not None
    assert aligned.shape == (512, 512, 3)


