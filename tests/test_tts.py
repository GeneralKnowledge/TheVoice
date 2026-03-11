from app.tts import CollectiveVoiceTTSClient, LocalToneFallbackTTS, build_tts_client, normalize_text


def test_build_tts_collective_client() -> None:
    client = build_tts_client("collective", None, 160)
    assert isinstance(client, CollectiveVoiceTTSClient)


def test_build_tts_unknown_provider_falls_back() -> None:
    client = build_tts_client("unknown", None, 160)
    assert isinstance(client, LocalToneFallbackTTS)


def test_normalize_text_collapses_whitespace_and_clamps() -> None:
    normalized = normalize_text("a\n\n b\t c")
    assert normalized == "a b c"
    assert len(normalize_text("x" * 1000)) == 420
