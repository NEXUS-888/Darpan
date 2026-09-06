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
    is_event_or_non_human_entity,
    is_official_profile_match,
    extract_candidate_entities_from_web_results,
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


def test_is_event_or_non_human_entity():
    # Tournaments, cups, competitions, years
    assert is_event_or_non_human_entity("Cricket World Cup 2019") is True
    assert is_event_or_non_human_entity("FIFA World Cup 2022") is True
    assert is_event_or_non_human_entity("ICC Champions Trophy") is True
    assert is_event_or_non_human_entity("IPL 2024") is True
    assert is_event_or_non_human_entity("T20 World Cup") is True
    assert is_event_or_non_human_entity("Premier League Season") is True

    # Real human identities must NOT be classified as events
    assert is_event_or_non_human_entity("Virat Kohli") is False
    assert is_event_or_non_human_entity("Cristiano Ronaldo") is False
    assert is_event_or_non_human_entity("Sam Altman") is False
    assert is_event_or_non_human_entity("Satya Nadella") is False


def test_extract_clean_identity_name_event_stripping():
    # Strips action and event phrases while keeping the human name
    assert extract_clean_identity_name("Virat Kohli during Cricket World Cup 2019") == "Virat Kohli"
    assert extract_clean_identity_name("Virat Kohli at ICC Cricket World Cup 2019") == "Virat Kohli"
    assert extract_clean_identity_name("Virat Kohli in action during World Cup") == "Virat Kohli"
    assert extract_clean_identity_name("Cristiano Ronaldo during FIFA World Cup 2022") == "Cristiano Ronaldo"


def test_wikidata_resolution_virat_kohli():
    canonical_title, snippet, matches = resolve_wikidata_socials(
        "Virat Kohli", "https://example.com/virat.jpg"
    )
    assert canonical_title == "Virat Kohli"
    assert len(matches) >= 3
    platforms = [m.platform for m in matches]
    assert "X (Twitter)" in platforms
    assert "Instagram" in platforms
    assert "Facebook" in platforms

    # Verify official flag is set on all Wikidata verified accounts
    for m in matches:
        assert m.is_official is True
        assert m.citation_type == "official_profile"

    tw = next(m for m in matches if m.platform == "X (Twitter)")
    assert tw.author_handle == "@imVkohli"
    assert "x.com/imVkohli" in tw.post_url

    ig = next(m for m in matches if m.platform == "Instagram")
    assert ig.author_handle == "@virat.kohli"
    assert "instagram.com/virat.kohli" in ig.post_url

    fb = next(m for m in matches if m.platform == "Facebook")
    assert fb.author_handle == "@virat.kohli"
    assert "facebook.com/virat.kohli" in fb.post_url


def test_is_official_profile_match():
    # 1. Matches with is_official=True are official
    m_official = SocialMatch(
        platform="Instagram",
        post_url="https://www.instagram.com/virat.kohli/",
        author_handle="@virat.kohli",
        post_title="Virat Kohli on Instagram",
        snippet="Official",
        matched_image_url="",
        discovery_timestamp=0,
        confidence_score=0.99,
        is_official=True,
    )
    assert is_official_profile_match(m_official, "Virat Kohli") is True

    # 2. Citation / usage posts (e.g. Facebook post by meme / fan page) are NOT official
    m_citation = SocialMatch(
        platform="Facebook",
        post_url="https://www.facebook.com/thewall19cool/posts/1015698745",
        author_handle="@thewall19cool",
        post_title="Jay Shah and Shami discussion",
        snippet="Shared photo during World Cup",
        matched_image_url="",
        discovery_timestamp=0,
        confidence_score=0.91,
    )
    assert is_official_profile_match(m_citation, "Virat Kohli") is False

    # 3. Reddit community discussion is NOT an official personal profile
    m_reddit = SocialMatch(
        platform="Reddit",
        post_url="https://www.reddit.com/r/Cricket/comments/abc123/kohli_cover_drive/",
        author_handle="r/Cricket",
        post_title="Discussion on cover drive",
        snippet="Reddit thread",
        matched_image_url="",
        discovery_timestamp=0,
        confidence_score=0.88,
    )
    assert is_official_profile_match(m_reddit, "Virat Kohli") is False

    # 4. Fan page post is NOT official
    m_fan = SocialMatch(
        platform="Instagram",
        post_url="https://www.instagram.com/kingkohlifans18/p/abc12345/",
        author_handle="@kingkohlifans18",
        post_title="King Kohli Fans post",
        snippet="Fan page updates",
        matched_image_url="",
        discovery_timestamp=0,
        confidence_score=0.85,
    )
    assert is_official_profile_match(m_fan, "Virat Kohli") is False

    # 5. Non-human event entity rejects personal official profile status
    assert is_official_profile_match(m_citation, "Cricket World Cup 2019") is False


def test_candidate_extraction_from_results():
    organic = [
        {"title": "Virat Kohli - Wikipedia", "link": "https://en.wikipedia.org/wiki/Virat_Kohli"},
        {"title": "Virat Kohli during Cricket World Cup 2019", "link": "https://facebook.com/thewall19cool/posts/123"},
    ]
    visual = [
        {"title": "Virat Kohli Wallpapers & Photos", "link": "https://instagram.com/kingkohlifans18/p/456"},
        {"title": "Virat Kohli in action", "link": "https://reddit.com/r/Cricket/comments/789"},
    ]
    kg_title = "Cricket World Cup 2019"  # Event title should be rejected

    cands = extract_candidate_entities_from_web_results(organic, visual, kg_title=kg_title)
    assert "Virat Kohli" in cands
    assert "Cricket World Cup 2019" not in cands


def test_search_gateway_separates_official_and_citations():
    # Simulate Serper Google Lens output where image was cited by fan page & event
    mock_serper_matches = [
        SocialMatch(
            platform="Facebook",
            post_url="https://www.facebook.com/thewall19cool/posts/1015698745",
            author_handle="@thewall19cool",
            post_title="Jay Shah and Shami at World Cup",
            snippet="Photo used in discussion",
            matched_image_url="https://serper.dev/thumb1.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.92,
            is_official=False,
            citation_type="citation",
        ),
        SocialMatch(
            platform="Reddit",
            post_url="https://www.reddit.com/r/Cricket/comments/abc123/kohli/",
            author_handle="r/Cricket",
            post_title="Cricket World Cup discussion",
            snippet="Reddit match thread",
            matched_image_url="https://serper.dev/thumb2.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.89,
            is_official=False,
            citation_type="citation",
        ),
        SocialMatch(
            platform="Instagram",
            post_url="https://www.instagram.com/virat.kohli/",
            author_handle="@virat.kohli",
            post_title="Virat Kohli (@virat.kohli) on Instagram",
            snippet="Official Instagram account of Virat Kohli.",
            matched_image_url="https://serper.dev/thumb3.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.99,
            is_official=True,
            citation_type="official_profile",
        ),
        SocialMatch(
            platform="X (Twitter)",
            post_url="https://x.com/imVkohli",
            author_handle="@imVkohli",
            post_title="Virat Kohli (@imVkohli) on X",
            snippet="Verified public profile for Virat Kohli.",
            matched_image_url="https://serper.dev/thumb4.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.99,
            is_official=True,
            citation_type="official_profile",
        ),
    ]

    mock_provider = MagicMock()
    mock_provider.search_face.return_value = mock_serper_matches
    mock_provider.last_detected_entity = "Virat Kohli"
    mock_provider.last_matched_image_urls = ["https://serper.dev/thumb1.jpg"]

    gw = SearchGateway(provider_type="auto")
    gw.provider = mock_provider

    res = gw.search_all("samples/demo_face.jpg")

    assert res.entity_name == "Virat Kohli"
    # Primary match must be an official verified profile, NOT the citation post @thewall19cool
    assert res.primary_match.is_official is True
    assert res.primary_match.author_handle in ("@virat.kohli", "@imVkohli")

    # Official profiles must contain Virat Kohli's verified accounts
    assert len(res.official_profiles) == 2
    off_handles = [m.author_handle for m in res.official_profiles]
    assert "@virat.kohli" in off_handles
    assert "@imVkohli" in off_handles

    # Image citations must contain the web citations where image was used
    assert len(res.image_citations) == 2
    cit_handles = [m.author_handle for m in res.image_citations]
    assert "@thewall19cool" in cit_handles
    assert "r/Cricket" in cit_handles

    # Summary dict must contain both categories
    summary = res.to_summary_dict()
    assert len(summary["official_profiles"]) == 2
    assert len(summary["image_citations"]) == 2
    assert len(summary["all_matches"]) == 4


def test_is_event_or_non_human_entity_known_phrases():
    # Known sports teams, publishers, and concepts must be identified as non-human
    assert is_event_or_non_human_entity("Team India") is True
    assert is_event_or_non_human_entity("Indian Test") is True
    assert is_event_or_non_human_entity("Routine Of Nepal Banda") is True
    assert is_event_or_non_human_entity("Social Media") is True
    assert is_event_or_non_human_entity("Full Video") is True
    assert is_event_or_non_human_entity("New Zealand") is True
    assert is_event_or_non_human_entity("Press Conference") is True

    # Real human identities must NOT be marked non-human
    assert is_event_or_non_human_entity("Virat Kohli") is False
    assert is_event_or_non_human_entity("Cristiano Ronaldo") is False
    assert is_event_or_non_human_entity("Sam Altman") is False


def test_candidate_extraction_from_long_sentence_titles():
    # Real visual search results often have full sentence titles rather than just the person's name.
    # The extractor must find 2-3 word proper noun n-grams ("Virat Kohli") and avoid returning 14-word sentences.
    visual = [
        {
            "title": "With pride in his eyes and the iconic Indian Test jersey, Virat Kohli stands tall.",
            "source": "cricket news",
            "link": "https://example.com/post1",
        },
        {
            "title": "Jay Shah said I saw Shami consistently taking wickets in the World Cup",
            "source": "sports daily",
            "link": "https://example.com/post2",
        },
        {
            "title": "Virat Kohli Wallpapers & Photos",
            "source": "fan club",
            "link": "https://example.com/post3",
        },
    ]
    organic = []
    cands = extract_candidate_entities_from_web_results(organic, visual)
    assert "Virat Kohli" in cands
    # Must NOT have extracted long sentences or non-person phrases
    for cand in cands:
        assert len(cand.split()) <= 4
        assert not is_event_or_non_human_entity(cand)
    assert "Indian Test" not in cands


def test_extract_clean_identity_name_year_boundary():
    # Years at the end of names must be stripped cleanly
    assert extract_clean_identity_name("Virat Kohli 2024") == "Virat Kohli"
    assert extract_clean_identity_name("Virat Kohli in 2023") == "Virat Kohli"
    assert extract_clean_identity_name("Virat Kohli (2019)") == "Virat Kohli"

    # Human name with year must not be falsely rejected as an event
    assert is_event_or_non_human_entity("Virat Kohli 2024") is False


def test_search_duckduckgo_socials_b_param():
    from src.social_search import search_duckduckgo_socials

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body></body></html>"
        mock_post.return_value = mock_resp

        search_duckduckgo_socials("Virat Kohli twitter", "https://example.com/pic.jpg")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert "data" in call_kwargs
        # Must include "b": "" so DuckDuckGo returns search HTML instead of language picker
        assert call_kwargs["data"].get("b") == ""


def test_is_event_or_non_human_entity_sports_teams():
    # National and club sports teams must be identified as non-human entities
    assert is_event_or_non_human_entity("India Cricket Team") is True
    assert is_event_or_non_human_entity("India national cricket team") is True
    assert is_event_or_non_human_entity("Indian Cricket Team") is True
    assert is_event_or_non_human_entity("cricket team") is True
    assert is_event_or_non_human_entity("national football team") is True
    assert is_event_or_non_human_entity("Cricket World Cup 2019") is True

    # Real human identities must NOT be rejected
    assert is_event_or_non_human_entity("Virat Kohli") is False
    assert is_event_or_non_human_entity("Cristiano Ronaldo") is False
    assert is_event_or_non_human_entity("Elon Musk") is False


def test_is_official_profile_match_rejects_videos_and_slugs():
    # 1. Video URL on social platforms must be rejected as an image citation, not official profile
    video_match = SocialMatch(
        platform="Facebook",
        post_url="https://www.facebook.com/ravinder.jawanda.14/videos/-team-india-conquers-england-from-grit-to-glory-the-men-in-blue-once-again-prove/1576856693927377/",
        author_handle="@ravinder.jawanda.14",
        post_title="Team India conquers England",
        snippet="Discovered identity post matching face scan.",
        matched_image_url="https://example.com/thumb.jpg",
        discovery_timestamp=12345,
        confidence_score=0.91,
    )
    assert is_official_profile_match(video_match, "Virat Kohli") is False
    assert is_official_profile_match(video_match, "India Cricket Team") is False

    # 2. Purely numeric user handle on Facebook must be rejected
    numeric_match = SocialMatch(
        platform="Facebook",
        post_url="https://www.facebook.com/100066924695053/posts/another-flat-track-stage-set-for-flat-track-bully-king-kohli/1185412483699564/",
        author_handle="@100066924695053",
        post_title="Another flat track stage set for flat track bully King kohli",
        snippet="Discovered identity post matching face scan.",
        matched_image_url="https://example.com/thumb.jpg",
        discovery_timestamp=12345,
        confidence_score=0.91,
    )
    assert is_official_profile_match(numeric_match, "Virat Kohli") is False

    # 3. Authentic official profile handles must be accepted
    official_x = SocialMatch(
        platform="X (Twitter)",
        post_url="https://x.com/imVkohli",
        author_handle="@imVkohli",
        post_title="@imVkohli on X (Twitter)",
        snippet="Verified public profile for Virat Kohli.",
        matched_image_url="https://example.com/thumb.jpg",
        discovery_timestamp=12345,
        confidence_score=0.98,
        is_official=True,
    )
    assert is_official_profile_match(official_x, "Virat Kohli") is True

    official_ig = SocialMatch(
        platform="Instagram",
        post_url="https://www.instagram.com/virat.kohli/",
        author_handle="@virat.kohli",
        post_title="@virat.kohli on Instagram",
        snippet="Verified public profile for Virat Kohli.",
        matched_image_url="https://example.com/thumb.jpg",
        discovery_timestamp=12345,
        confidence_score=0.98,
    )
    assert is_official_profile_match(official_ig, "Virat Kohli") is True


def test_extract_candidate_entities_possessive_relations():
    """
    Tests that possessive relations ('X's girlfriend Y', 'Y support her boyfriend X')
    prioritize the actual subject Y (Ines Garcia) over the referenced celebrity X (Lamine Yamal),
    and filters out sports venues/stadiums ('Camp Nou').
    """
    items = [
        {
            "title": "🚨 NEW: Lamine Yamal's girlfriend Ines Garcia has visited Camp Nou today to watch her boyfriend's match!",
            "snippet": "She wrote on (IG): “First time at the Camp Nou! watching my 👶🏾”",
            "link": "https://www.instagram.com/p/DcPBDifkoOt/",
        },
        {
            "title": "Ines Garcia for the first time at the Camp Nou to support her boyfriend Lamine Yamal in the Barcelona match against Al Ahly",
            "snippet": "Ines Garcia Camp Nou photos",
            "link": "https://www.instagram.com/p/DcPHGvADFZX/",
        },
        {
            "title": "Ines Garcia Hit by A Ball | TikTok",
            "snippet": "TikTok discovery video",
            "link": "https://www.tiktok.com/discover/ines-garcia-hit-by-a-ball",
        },
    ]

    cands = extract_candidate_entities_from_web_results(items, [])
    assert "Ines Garcia" in cands
    assert "Camp Nou" not in cands
    # Ines Garcia should be ranked ahead of Lamine Yamal
    if "Lamine Yamal" in cands:
        assert cands.index("Ines Garcia") < cands.index("Lamine Yamal")


def test_is_event_or_non_human_entity_stadiums_and_venues():
    """
    Ensures famous stadiums, arenas, and sports clubs are filtered as non-person entities.
    """
    assert is_event_or_non_human_entity("Camp Nou") is True
    assert is_event_or_non_human_entity("Santiago Bernabeu") is True
    assert is_event_or_non_human_entity("Old Trafford") is True
    assert is_event_or_non_human_entity("San Siro") is True
    assert is_event_or_non_human_entity("Wankhede Stadium") is True
    assert is_event_or_non_human_entity("Al Ahly") is True


def test_resolve_wikidata_socials_extracts_p18_portrait():
    """
    Verifies that resolve_wikidata_socials populates matched_image_url with the entity's
    official Wikimedia Commons P18 portrait, rather than echoing the query image.
    """
    query_thumb = "https://example.com/query_crop.jpg"
    canon_title, bio, matches = resolve_wikidata_socials("Virat Kohli", query_thumb)
    assert canon_title == "Virat Kohli"
    assert len(matches) > 0
    # Every official profile should point to the Wikimedia Commons portrait URL, NOT query_thumb
    for m in matches:
        assert m.matched_image_url != query_thumb
        assert "commons.wikimedia.org" in m.matched_image_url or "upload.wikimedia.org" in m.matched_image_url


def test_regular_person_web_discovery_priority_when_no_official_profiles():
    """
    Verifies that for regular/unknown people without verified Wikidata celebrity profiles,
    the primary match is the direct web citation post URL where their photo was found.
    """
    from unittest.mock import patch, MagicMock
    from src.social_search import SearchGateway

    # Mock provider returning direct web citations (Reddit, TikTok, Instagram post)
    mock_provider = MagicMock()
    mock_provider.last_detected_entity = "Ines Garcia"
    mock_provider.last_matched_image_urls = ["https://preview.redd.it/photo.jpg"]
    mock_provider.search_face.return_value = [
        SocialMatch(
            platform="Reddit",
            post_url="https://www.reddit.com/r/trueratecelebrities/comments/1vend7w/whos_the_betterlooking_wag/",
            author_handle="r/trueratecelebrities",
            post_title="Who's the better-looking WAG? : r/trueratecelebrities",
            snippet="Discussion thread with photo",
            matched_image_url="https://preview.redd.it/photo.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.92,
            is_official=False,
            citation_type="citation",
        ),
        SocialMatch(
            platform="TikTok",
            post_url="https://www.tiktok.com/@inees_gaarcia1/video/7673808331114384673",
            author_handle="@inees_gaarcia1",
            post_title="TikTok video with photo",
            snippet="TikTok video description",
            matched_image_url="https://tiktok.com/thumb.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.90,
            is_official=False,
            citation_type="citation",
        )
    ]

    gateway = SearchGateway(provider_type="auto")
    gateway.provider = mock_provider

    # Without verified celebrity Wikidata accounts, primary_match must be the direct citation link
    with patch("src.social_search.resolve_wikidata_socials", return_value=(None, "", [])):
        res = gateway.search_all("dummy_crop.jpg")
        assert len(res.official_profiles) == 0
        assert len(res.image_citations) >= 2
        assert res.primary_match.post_url == "https://www.reddit.com/r/trueratecelebrities/comments/1vend7w/whos_the_betterlooking_wag/"
        assert res.primary_match.citation_type == "citation"


def test_search_gateway_rejects_wikidata_candidate_when_biometrics_mismatch():
    """
    Verifies that when a candidate (e.g. Lamine Yamal) is resolved by Wikidata,
    but biometrics against his P18 portrait fail (e.g. girl face scan vs male footballer portrait),
    SearchGateway rejects the candidate and does NOT bind his identity or official profiles.
    """
    from unittest.mock import patch, MagicMock
    from src.social_search import SearchGateway

    mock_provider = MagicMock()
    mock_provider.last_detected_entity = None
    mock_provider.last_matched_image_urls = ["https://preview.redd.it/photo.jpg"]
    mock_provider.search_face.return_value = [
        SocialMatch(
            platform="Reddit",
            post_url="https://www.reddit.com/r/trueratecelebrities/comments/1vend7w/wag/",
            author_handle="r/trueratecelebrities",
            post_title="Lamine Yamal's girlfriend Ines Garcia",
            snippet="Photo of Ines Garcia",
            matched_image_url="https://preview.redd.it/photo.jpg",
            discovery_timestamp=1700000000,
            confidence_score=0.92,
            is_official=False,
            citation_type="citation",
        )
    ]

    gateway = SearchGateway(provider_type="auto")
    gateway.provider = mock_provider

    # Mock Wikidata returning Lamine Yamal with his official P18 portrait
    lamine_p18 = "https://commons.wikimedia.org/wiki/Special:FilePath/Lamine_Yamal.jpg"
    lamine_matches = [
        SocialMatch(
            platform="Instagram",
            post_url="https://www.instagram.com/lamineyamal/",
            author_handle="@lamineyamal",
            post_title="Lamine Yamal on Instagram",
            snippet="Official Instagram account of Lamine Yamal.",
            matched_image_url=lamine_p18,
            discovery_timestamp=1700000000,
            confidence_score=0.99,
            is_official=True,
            citation_type="official_profile",
        )
    ]

    def mock_resolve(name, thumb):
        if "yamal" in name.lower():
            return "Lamine Yamal", "Spanish footballer", lamine_matches
        return None, "", []

    # Mock face_engine returning low similarity (0.07) for portrait mismatch
    mock_fe = MagicMock()
    mock_fe.compute_similarity.return_value = MagicMock(score=0.07, verified=False)

    with patch("src.social_search.resolve_wikidata_socials", side_effect=mock_resolve), \
         patch("src.social_search._get_biometric_face_engine", return_value=mock_fe):
        res = gateway.search_all("output/uploaded_face.jpg", fallback_image_path="output/uploaded_face.jpg")
        # Candidate Lamine Yamal must be rejected!
        assert res.entity_name != "Lamine Yamal"
        assert len(res.official_profiles) == 0
        assert res.primary_match.post_url == "https://www.reddit.com/r/trueratecelebrities/comments/1vend7w/wag/"





