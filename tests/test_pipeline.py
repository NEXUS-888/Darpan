"""
End-to-End Integration test for the DarpanPipeline.
"""
import os
import pytest
from src.pipeline import DarpanPipeline, VeriFacePipeline


def test_pipeline_execution_end_to_end(tmp_path):
    sample_img = os.path.join(os.path.dirname(__file__), "..", "samples", "demo_face.jpg")
    if not os.path.exists(sample_img):
        pytest.skip("sample demo_face.jpg not found")

    out_dir = str(tmp_path / "test_out")
    pipeline = DarpanPipeline(
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
    assert "official_profiles" in receipt["social_discovery_summary"]
    assert "image_citations" in receipt["social_discovery_summary"]
    assert isinstance(receipt["social_discovery_summary"]["official_profiles"], list)
    assert isinstance(receipt["social_discovery_summary"]["image_citations"], list)
    assert receipt["verification_status"]["on_chain_confirmed"] is True


def test_pipeline_execution_with_virat_kohli_hint(tmp_path):
    sample_img = os.path.join(os.path.dirname(__file__), "..", "samples", "demo_face.jpg")
    if not os.path.exists(sample_img):
        pytest.skip("sample demo_face.jpg not found")

    out_dir = str(tmp_path / "test_out_virat")
    pipeline = DarpanPipeline(
        network="local",
        search_provider="auto",
        output_dir=out_dir,
    )

    receipt = pipeline.execute(sample_img, subject_hint="Virat Kohli")
    assert receipt["pipeline_status"] == "COMPLETED"
    assert receipt["social_discovery_summary"]["entity_name"] == "Virat Kohli"
    assert "official_profiles" in receipt["social_discovery_summary"]
    assert "image_citations" in receipt["social_discovery_summary"]
    assert len(receipt["social_discovery_summary"]["official_profiles"]) >= 2
    assert any(
        m["author_handle"] == "@virat.kohli" or m["author_handle"] == "@imVkohli"
        for m in receipt["social_discovery_summary"]["official_profiles"]
    )
    assert receipt["verification_status"]["on_chain_confirmed"] is True


