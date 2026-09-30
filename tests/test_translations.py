"""Translation resource consistency tests."""

import json
from pathlib import Path


def test_translation_keys_match():
    """English and Polish translation resources have matching structure."""
    root = Path(__file__).parents[1] / "custom_components/rest_assistant"
    strings = json.loads((root / "strings.json").read_text(encoding="utf-8"))

    def key_shape(value):
        if isinstance(value, dict):
            return {key: key_shape(item) for key, item in value.items()}
        return None

    for language in ("en", "pl"):
        translation = json.loads(
            (root / "translations" / f"{language}.json").read_text(encoding="utf-8")
        )
        assert key_shape(translation) == key_shape(strings)
