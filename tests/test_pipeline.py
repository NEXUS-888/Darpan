"""
End-to-End Integration test for the VeriFacePipeline.
"""
import os
import pytest
from src.pipeline import VeriFacePipeline


def test_pipeline_execution_end_to_end(tmp_path):
    sample_img = os.path.join(os.path.dirname(__file__), "..", "samples", "demo_face.jpg")
    if not os.path.exists(sample_img):
        pytest.skip("sample demo_face.jpg not found")

    out_dir = str(tmp_path / "test_out")
    pipeline = VeriFacePipeline(
        network="local",
        search_provider="eval",
        output_dir=out_dir,
    )

    receipt = pipeline.execute(sample_img)

    assert receipt["pipeline_status"] == "COMPLETED"
    assert receipt["input_image"]["face_detected"] is True
    assert receipt["discovered_social_post"]["post_url"].startswith("https://")
    assert receipt["cryptography"]["attestation_id"].startswith("0x")
    assert receipt["blockchain"]["status"] == "SUCCESS"
    assert receipt["verification_status"]["on_chain_confirmed"] is True
    assert os.path.exists(os.path.join(out_dir, "attestation_receipt.json"))


def test_pipeline_execution_all_engines(tmp_path):
    sample_img = os.path.join(os.path.dirname(__file__), "..", "samples", "demo_face.jpg")
    if not os.path.exists(sample_img):
        pytest.skip("sample demo_face.jpg not found")

    out_dir = str(tmp_path / "test_out_all_engines")
    pipeline = VeriFacePipeline(
        network="local",
        search_provider="all-engines",
        output_dir=out_dir,
    )

    receipt = pipeline.execute(sample_img, subject_hint="Cristiano Ronaldo")

    assert receipt["pipeline_status"] == "COMPLETED"
    assert receipt["input_image"]["face_detected"] is True
    assert receipt["discovered_social_post"]["post_url"].startswith("https://")
    assert receipt["social_discovery_summary"]["search_engine_used"].startswith("Federated Multi-Engine")
    assert receipt["social_discovery_summary"]["entity_name"] == "Cristiano Ronaldo"
    assert receipt["verification_status"]["on_chain_confirmed"] is True

