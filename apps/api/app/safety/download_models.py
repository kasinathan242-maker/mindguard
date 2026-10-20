"""Download the pinned sentence encoder used by the safety classifier.

    uv run python -m app.safety.download_models

The Docker image runs the same download at build time, so containers work fully offline.
"""

from huggingface_hub import snapshot_download

ENCODER = "intfloat/multilingual-e5-small"
ENCODER_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
ENCODER_FILES = [
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentencepiece.bpe.model",
]


def main() -> None:
    path = snapshot_download(ENCODER, revision=ENCODER_REVISION, allow_patterns=ENCODER_FILES)
    print(f"{ENCODER}@{ENCODER_REVISION[:8]} ready in {path}")


if __name__ == "__main__":
    main()
