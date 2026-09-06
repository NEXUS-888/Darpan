"""
Unit tests for the social media and web search gateway with dynamic identity resolution.
"""
import os
from unittest.mock import patch, MagicMock
from src.social_search import (
    identify_social_platform,
    extract_author_handle,
    extract_clean_identity_name,
    SearchGateway,
    DynamicIdentityResolver,
    YandexProvider,
    FederatedSearchProvider,
    yandex_reverse_visual_search,
    bing_reverse_visual_search,
    SocialMatch,
    SearchResult,
    resolve_wikidata_socials,
    normalize_social_url,
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
    assert "X (Twitter)" in res.platforms_found or "Instagram" in res.platforms_found
    assert res.primary_match.author_handle.lower() == "@cristiano"
    assert res.primary_match.platform in ("X (Twitter)", "Instagram")
    assert "cristiano" in res.primary_match.post_url.lower()

    canonical = res.primary_match.to_canonical_dict()
    assert "post_url" in canonical
    assert "author_handle" in canonical
    assert canonical["author_handle"].lower() == "@cristiano"


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


def test_extract_clean_identity_name_founders():
    assert extract_clean_identity_name("Guillermo Rauch - CEO & Founder - Vercel | LinkedIn") == "Guillermo Rauch"
    assert extract_clean_identity_name("Alexandr Wang (@alexandr_wang) / X") == "Alexandr Wang"
    assert extract_clean_identity_name("Pieter Levels (@levelsio) on X: 'Just launched my new AI startup...'") == "Pieter Levels"
    assert extract_clean_identity_name("Nikita Bier, Founder of Gas and tbh - TechCrunch") == "Nikita Bier"
    assert extract_clean_identity_name("Amjad Masad - Replit CEO on The Joe Rogan Experience - YouTube") == "Amjad Masad"


def test_identify_tech_platforms():
    assert identify_social_platform("https://substack.com/@techfounder") == "Substack"
    assert identify_social_platform("https://techcrunch.com/2023/10/founder-series/") == "TechCrunch"
    assert identify_social_platform("https://www.producthunt.com/@levelsio") == "Product Hunt"
    assert identify_social_platform("https://news.ycombinator.com/user?id=rauchg") == "Hacker News"


def test_yandex_reverse_visual_search_parsing():
    html_mock = """
    <html>
      <head><title>Cristiano Ronaldo — Yandex Images</title></head>
      <body>
        <div class="CbirTags-Item"><a href="#">Cristiano Ronaldo</a></div>
        <div class="CbirTags-Item"><a href="#">football player</a></div>
        <a href="https://www.instagram.com/cristiano/">Instagram Profile</a>
        <a href="https://x.com/Cristiano">X Account</a>
        <img src="//avatars.mds.yandex.net/i?id=test12345-images-thumbs&n=13" />
        <a href="https://example.com/photo.jpg">Direct Photo</a>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = html_mock

    with patch("requests.get", return_value=mock_resp):
        # 1. 2-tuple return (default)
        entity, urls = yandex_reverse_visual_search("https://example.com/input.jpg", return_images=False)
        assert entity == "Cristiano Ronaldo"
        assert "https://www.instagram.com/cristiano/" in urls
        assert "https://x.com/Cristiano" in urls

        # 2. 3-tuple return (with images)
        entity, urls, imgs = yandex_reverse_visual_search("https://example.com/input.jpg", return_images=True)
        assert entity == "Cristiano Ronaldo"
        assert len(imgs) >= 2
        assert any("avatars.mds.yandex.net" in img for img in imgs)
        assert any("example.com/photo.jpg" in img for img in imgs)


def test_yandex_reverse_visual_search_error_handling():
    with patch("requests.get", side_effect=Exception("Connection timed out")):
        entity, urls = yandex_reverse_visual_search("https://example.com/test.jpg", return_images=False)
        assert entity is None
        assert urls == []

        entity, urls, imgs = yandex_reverse_visual_search("https://example.com/test.jpg", return_images=True)
        assert entity is None
        assert urls == []
        assert imgs == []


def test_yandex_provider_and_gateway():
    gateway = SearchGateway(provider_type="yandex")
    assert isinstance(gateway.provider, YandexProvider)

    # Search with subject hint using yandex provider
    res = gateway.search_all("samples/demo_face.jpg", subject_hint="Cristiano Ronaldo")
    assert res is not None
    assert res.search_engine_used == "Yandex Reverse Visual Search"
    assert res.total_platforms >= 3
    assert any(m.platform == "X (Twitter)" for m in res.all_matches)
    assert res.primary_match.author_handle == "@Cristiano"


def test_social_match_biometric_similarity():
    match = SocialMatch(
        platform="Instagram",
        post_url="https://instagram.com/cristiano",
        author_handle="@cristiano",
        post_title="Cristiano on Instagram",
        snippet="Verified profile",
        matched_image_url="https://example.com/pic.jpg",
        discovery_timestamp=123456789,
        confidence_score=0.97,
    )
    assert match.biometric_similarity is None
    d1 = match.to_canonical_dict()
    assert "biometric_similarity" not in d1

    updated = match.with_biometric_similarity(0.941234)
    assert updated.biometric_similarity == 0.941234
    d2 = updated.to_canonical_dict()
    assert "biometric_similarity" in d2
    assert d2["biometric_similarity"] == 0.9412


def test_normalize_social_url():
    # 1. Scheme and www normalization
    assert normalize_social_url("http://www.instagram.com/cristiano/") == "https://instagram.com/cristiano"
    assert normalize_social_url("https://instagram.com/cristiano") == "https://instagram.com/cristiano"

    # 2. Twitter / X canonicalization
    assert normalize_social_url("https://twitter.com/Cristiano") == "https://x.com/cristiano"
    assert normalize_social_url("https://x.com/Cristiano/") == "https://x.com/cristiano"

    # 3. Protocol-relative URLs
    assert normalize_social_url("//x.com/testuser") == "https://x.com/testuser"

    # 4. Tracking and transient query parameters stripped
    assert normalize_social_url("https://x.com/Cristiano?s=20&t=123") == "https://x.com/cristiano"
    assert normalize_social_url("https://www.instagram.com/cristiano/?hl=en&utm_source=ig_web") == "https://instagram.com/cristiano"

    # 5. Empty / invalid handling
    assert normalize_social_url("") == ""
    assert normalize_social_url(None) == ""


def test_search_gateway_all_engines_provider_selection():
    # 1. Standard "all-engines"
    gw = SearchGateway(provider_type="all-engines")
    assert isinstance(gw.provider, FederatedSearchProvider)
    assert gw.provider.engine_name.startswith("Federated Multi-Engine")

    # 2. Aliases
    gw_fed = SearchGateway(provider_type="federated")
    assert isinstance(gw_fed.provider, FederatedSearchProvider)

    gw_all = SearchGateway(provider_type="all_engines")
    assert isinstance(gw_all.provider, FederatedSearchProvider)

    # 3. Engine name with API key
    gw_key = SearchGateway(provider_type="all-engines", api_key="dummy_serper_key")
    assert gw_key.provider.engine_name == "Federated Multi-Engine (Yandex + Bing + Google Lens)"

    # 4. Explicit empty api_key="" disables Serper even when SERPER_API_KEY is in .env
    gw_nokey = SearchGateway(provider_type="all-engines", api_key="")
    assert gw_nokey.provider.engine_name == "Federated Multi-Engine (Yandex + Bing)"


def test_federated_search_aggregation_and_deduplication():
    # Mock Yandex returns with twitter.com and www.instagram.com with trailing slash
    mock_yandex = (
        "Cristiano Ronaldo",
        ["https://www.instagram.com/cristiano/", "https://twitter.com/Cristiano"],
        ["https://avatars.yandex.net/img1.jpg", "https://shared.com/face.jpg"]
    )
    # Mock Bing returns with x.com and non-www instagram.com without slash
    mock_bing = (
        "Cristiano Ronaldo",
        ["https://x.com/Cristiano", "https://instagram.com/cristiano", "https://github.com/torvalds"],
        ["https://bing.net/img2.jpg", "https://shared.com/face.jpg", "//bing.net/thumb_proto.jpg"]
    )
    # Mock Serper returns
    serper_mock_match = SocialMatch(
        platform="LinkedIn",
        post_url="https://linkedin.com/in/cristiano",
        author_handle="in/cristiano",
        post_title="Cristiano Ronaldo on LinkedIn",
        snippet="Verified LinkedIn profile",
        matched_image_url="https://serper.dev/img3.jpg",
        discovery_timestamp=1700000000,
        confidence_score=0.96,
    )

    with patch("src.social_search.yandex_reverse_visual_search", return_value=mock_yandex), \
         patch("src.social_search.bing_reverse_visual_search", return_value=mock_bing), \
         patch("src.social_search.SerperProvider.search_face", return_value=[serper_mock_match]), \
         patch("src.social_search.resolve_wikidata_socials", return_value=("Cristiano Ronaldo", "bio", [])):

        gw = SearchGateway(provider_type="all-engines", api_key="test_serper_key")
        res = gw.search_all("samples/demo_face.jpg")

        assert res is not None
        assert res.search_engine_used == "Federated Multi-Engine (Yandex + Bing + Google Lens)"
        assert res.entity_name == "Cristiano Ronaldo"

        # Check candidate face thumbnails deduplication: shared.com/face.jpg only once, protocol-relative normalized
        images = res.matched_image_urls
        assert len(images) == len(set(images))
        assert "https://avatars.yandex.net/img1.jpg" in images
        assert "https://bing.net/img2.jpg" in images
        assert "https://shared.com/face.jpg" in images
        assert "https://bing.net/thumb_proto.jpg" in images
        assert "https://serper.dev/img3.jpg" in images

        # Check platforms found
        platforms = res.platforms_found
        assert "Instagram" in platforms
        assert "X (Twitter)" in platforms
        assert "GitHub" in platforms
        assert "LinkedIn" in platforms

        # Check cross-domain post_url deduplication:
        # 1. twitter.com/Cristiano and x.com/Cristiano deduplicated to 1 match
        x_matches = [m for m in res.all_matches if m.platform == "X (Twitter)"]
        assert len(x_matches) == 1

        # 2. www.instagram.com/cristiano/ and instagram.com/cristiano deduplicated to 1 match
        ig_matches = [m for m in res.all_matches if m.platform == "Instagram"]
        assert len(ig_matches) == 1

        # Check summary property and to_summary_dict output
        assert res.summary == res.to_summary_dict()
        summary = res.summary
        assert summary["total_platforms"] == res.total_platforms
        assert summary["search_engine_used"] == "Federated Multi-Engine (Yandex + Bing + Google Lens)"
        assert summary["entity_name"] == "Cristiano Ronaldo"
        assert len(summary["all_matches"]) == len(res.all_matches)


def test_federated_search_local_image_does_not_double_upload():
    upload_calls = []

    def mock_uploader(path):
        upload_calls.append(path)
        return "https://hosted.test/uploaded_face.jpg"

    mock_yandex = ("Cristiano Ronaldo", [], [])
    mock_bing = ("Cristiano Ronaldo", [], [])

    with patch("src.social_search.upload_temp_image", side_effect=mock_uploader), \
         patch("src.social_search.yandex_reverse_visual_search", return_value=mock_yandex), \
         patch("src.social_search.bing_reverse_visual_search", return_value=mock_bing), \
         patch("src.social_search.SerperProvider.search_face", return_value=[]) as mock_serper_search, \
         patch("src.social_search.resolve_wikidata_socials", return_value=("Cristiano Ronaldo", "bio", [])):

        gw = SearchGateway(provider_type="all-engines", api_key="test_key")
        res = gw.search_all("samples/demo_face.jpg")

        assert res is not None
        # SerperProvider should have received the uploaded HTTP URL, avoiding double upload
        mock_serper_search.assert_called_once()
        passed_url = mock_serper_search.call_args[1]["image_path_or_url"]
        assert passed_url == "https://hosted.test/uploaded_face.jpg"


def test_federated_search_unindexed_fallback():
    mock_empty_yandex = (None, [], [])
    mock_empty_bing = (None, [], [])

    with patch("src.social_search.yandex_reverse_visual_search", return_value=mock_empty_yandex), \
         patch("src.social_search.bing_reverse_visual_search", return_value=mock_empty_bing), \
         patch("src.social_search.SerperProvider.search_face", return_value=[]):

        gw = SearchGateway(provider_type="all-engines", api_key="test_key")
        res = gw.search_all("samples/unindexed_face.jpg")

        assert res is not None
        assert res.total_platforms == 1
        assert res.primary_match.platform == "Biometric Identity Ledger"
        assert res.search_engine_used == "Federated Multi-Engine (Yandex + Bing + Google Lens)"


def test_federated_search_with_subject_hint():
    gw = SearchGateway(provider_type="all-engines")
    res = gw.search_all("samples/demo_face.jpg", subject_hint="Cristiano Ronaldo")

    assert res is not None
    assert res.entity_name == "Cristiano Ronaldo"
    assert res.total_platforms >= 3
    assert res.search_engine_used.startswith("Federated Multi-Engine")
    assert any(m.platform == "X (Twitter)" for m in res.all_matches)
    assert res.primary_match.author_handle == "@Cristiano"


def test_extract_clean_identity_name_descriptors():
    assert extract_clean_identity_name("Cristiano Ronaldo Portugal") == "Cristiano Ronaldo"
    assert extract_clean_identity_name("Cristiano Ronaldo Al-Nassr") == "Cristiano Ronaldo"
    assert extract_clean_identity_name("Sam Altman OpenAI") == "Sam Altman"
    assert extract_clean_identity_name("Lionel Messi Argentina") == "Lionel Messi"
    assert extract_clean_identity_name("Virat Kohli India") == "Virat Kohli"


def test_extract_author_handle_junk_filtering():
    # YouTube video URLs should not return @watch
    yt_handle = extract_author_handle("https://www.youtube.com/watch?v=jkymEEuIhlI", "YouTube")
    assert yt_handle != "@watch"

    # Instagram reel URLs should not return @reel or @reels
    ig_reel_handle = extract_author_handle("https://www.instagram.com/reel/DbjM7PQKXZP/", "Instagram")
    assert ig_reel_handle not in ("@reel", "@reels")

    # Long junk captions / hashtags > 30 chars must be rejected
    # LinkedIn advice / learning / pulse paths should not return advice/0 or @advice
    li_advice_handle = extract_author_handle(
        "https://www.linkedin.com/advice/0/what-to-do-when-you-want-to-switch-careers",
        "LinkedIn"
    )
    assert "advice/0" not in li_advice_handle
    assert li_advice_handle != "@advice"

    # LinkedIn in/profile should extract cleanly
    li_profile = extract_author_handle("https://www.linkedin.com/in/satyanadella", "LinkedIn")
    assert li_profile == "in/satyanadella"


def test_progressive_wikidata_resolution_with_country_descriptors():
    canonical_title, snippet, matches = resolve_wikidata_socials(
        "Cristiano Ronaldo Portugal", "https://example.com/test.jpg"
    )
    assert canonical_title == "Cristiano Ronaldo"
    assert len(matches) >= 3
    handles = [m.author_handle for m in matches]
    assert "@Cristiano" in handles or "@cristiano" in handles
