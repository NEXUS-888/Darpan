"""
Unit tests for the social media and web search gateway.
"""
from src.social_search import (
    identify_social_platform,
    extract_author_handle,
    SearchGateway,
    LocalEvaluationProvider,
)


def test_identify_social_platform():
    assert identify_social_platform("https://twitter.com/elonmusk/status/123") == "X (Twitter)"
    assert identify_social_platform("https://x.com/satya_nadella") == "X (Twitter)"
    assert identify_social_platform("https://www.linkedin.com/in/williamhgates") == "LinkedIn"
    assert identify_social_platform("https://reddit.com/r/ethereum") == "Reddit"
    assert identify_social_platform("https://github.com/torvalds") == "GitHub"
    assert identify_social_platform("https://example.com/random") is None


def test_extract_author_handle():
    assert extract_author_handle("https://x.com/tech_guru/status/987", "X (Twitter)") == "@tech_guru"
    assert extract_author_handle("https://github.com/octocat", "GitHub") == "@octocat"


def test_search_gateway_eval_provider():
    gateway = SearchGateway(provider_type="eval")
    match = gateway.search("samples/demo_face.jpg")
    assert match is not None
    assert match.platform in ["X (Twitter)", "LinkedIn", "Reddit"]
    assert match.post_url.startswith("https://")
    assert match.confidence_score > 0.8
    canonical = match.to_canonical_dict()
    assert "post_url" in canonical
    assert "author_handle" in canonical
