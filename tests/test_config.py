from camrahd_ai.config import _deep_merge, load_config


def test_deep_merge_overrides_nested_keys():
    base = {"llm": {"provider": "openai", "model": "gpt-5.5"}, "rag": {"mode": "hybrid"}}
    override = {"llm": {"model": "gpt-4o"}}
    merged = _deep_merge(base, override)
    assert merged["llm"]["model"] == "gpt-4o"
    assert merged["llm"]["provider"] == "openai"
    assert merged["rag"]["mode"] == "hybrid"


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    _deep_merge(base, {"a": {"b": 2}})
    assert base["a"]["b"] == 1


def test_load_config_has_required_sections():
    config = load_config()
    for section in ("llm", "embeddings", "rag", "memory"):
        assert section in config
