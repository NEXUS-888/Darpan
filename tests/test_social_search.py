"""
Unit tests for the social media and web search gateway with dynamic identity resolution.
"""
from src.social_search import (
    identify_social_platform,
    extract_author_handle,
    SearchGateway,
    DynamicIdentityResolver,
    resolve_wikidata_socials,
)


def test_identify_social_platform():
    assert identify_social_platform("https://twitter.com/elonmusk/status/123") == "X (Twitter)"
    assert identify_social_platform("https://x.com/Cristiano") == "X (Twitter)"
    assert identify_social_platform("https://www.instagram.com/cristiano/") == "Instagram"
    assert identify_social_platform("https://www.facebook.com/Cristiano") == "Facebook"
    assert identify_social_platform("https://www.linkedin.com/in/williamhgates") == "LinkedIn"
    assert identify_social_platform("https://reddit.com/r/ethereum") == "Reddit"
    assert identify_social_platform("https://github.com/torvalds") == "GitHub"
    assert identify_social_platform("https://www.youtube.com/channel/UC123") == "YouTube"
    assert identify_social_platform("https://example.com/random") is None


def test_extract_author_handle():
    assert extract_author_handle("https://x.com/Cristiano", "X (Twitter)") == "@Cristiano"
    assert extract_author_handle("https://instagram.com/cristiano/", "Instagram") == "@cristiano"
    assert extract_author_handle("https://github.com/torvalds", "GitHub") == "@torvalds"
    assert extract_author_handle("https://linkedin.com/in/satyanadella", "LinkedIn") == "in/satyanadella"


def test_wikidata_resolution_ronaldo():
    canonical_title, snippet, matches = resolve_wikidata_socials(
        "Cristiano Ronaldo", "https://iili.io/nJOxtQR.jpg"
    )
    assert canonical_title == "Cristiano Ronaldo"
    assert len(matches) >= 3
    platforms = [m.platform for m in matches]
    assert "X (Twitter)" in platforms
    assert "Instagram" in platforms

    # Find twitter match
    tw = next(m for m in matches if m.platform == "X (Twitter)")
    assert tw.author_handle == "@Cristiano"
    assert "x.com/Cristiano" in tw.post_url

    # Find instagram match
    ig = next(m for m in matches if m.platform == "Instagram")
    assert ig.author_handle == "@cristiano"
    assert "instagram.com/cristiano" in ig.post_url


def test_search_gateway_dynamic_ronaldo():
    gateway = SearchGateway(provider_type="auto")
    res = gateway.search_all("output/uploaded_face.jpg", subject_hint="Cristiano Ronaldo")
    assert res is not None
    assert res.total_platforms >= 3
    assert "X (Twitter)" in res.platforms_found
    assert res.primary_match.author_handle == "@Cristiano"
    assert res.primary_match.post_url == "https://x.com/Cristiano"

    canonical = res.primary_match.to_canonical_dict()
    assert "post_url" in canonical
    assert "author_handle" in canonical
    assert canonical["author_handle"] == "@Cristiano"


def test_search_gateway_unindexed_private_face():
    gateway = SearchGateway(provider_type="auto")
    # Query an arbitrary nonexistent face path with no hint
    res = gateway.search_all("samples/unindexed_face.jpg")
    assert res is not None
    assert res.total_platforms == 1
    assert res.primary_match.platform == "Biometric Identity Ledger"
    assert "veriface.protocol" not in res.primary_match.post_url
    assert res.primary_match.post_url.startswith("https://")
    assert "tech_innovator" not in res.primary_match.author_handle
    assert "VishalG" not in res.primary_match.author_handle


def test_search_gateway_url_hint():
    gateway = SearchGateway(provider_type="auto")
    res = gateway.search_all(
        "samples/demo_face.jpg",
        subject_hint="https://instagram.com/verified_creator"
    )
    assert res is not None
    assert res.primary_match.platform == "Instagram"
    assert res.primary_match.author_handle == "@verified_creator"
    assert res.primary_match.post_url == "https://instagram.com/verified_creator"


def test_search_gateway_handle_hint():
    gateway = SearchGateway(provider_type="auto")
    res = gateway.search_all(
        "samples/demo_face.jpg",
        subject_hint="@creator_user"
    )
    assert res is not None
    assert res.total_platforms >= 3
    assert any(m.author_handle == "@creator_user" for m in res.all_matches)
    urls = [m.post_url for m in res.all_matches]
    assert any("x.com/creator_user" in u for u in urls)
    assert any("instagram.com/creator_user" in u for u in urls)

