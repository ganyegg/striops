from striops.reasoning import MockProvider


def test_mock_is_deterministic():
    p = MockProvider()
    assert p.generate("hello world") == p.generate("hello world")
    assert p.embed("x") == p.embed("x")


def test_mock_embedding_dimension():
    assert len(MockProvider().embed("anything")) == 768


def test_mock_json_shape():
    out = MockProvider().generate_json("summarise this")
    assert "summary" in out and "confidence" in out
