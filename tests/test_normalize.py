from core.nlp.text_clean import normalize

def test_normalize():
    t = normalize("Hello! Email me at test@example.com https://example.com 123")
    assert "email" in t
    assert "url" in t
    assert "num" in t
