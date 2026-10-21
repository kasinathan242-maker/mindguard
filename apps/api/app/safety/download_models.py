"""Download the pinned models: the safety sentence encoder and the text emotion model.

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


EMOTION_FILES = [
    "config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "vocab.json",
    "merges.txt",
]


def main() -> None:
    from app.emotion.model import MODEL, REVISION

    for repo, revision, files in (
        (ENCODER, ENCODER_REVISION, ENCODER_FILES),
        (MODEL, REVISION, EMOTION_FILES),
    ):
        path = snapshot_download(repo, revision=revision, allow_patterns=files)
        print(f"{repo}@{revision[:8]} ready in {path}")


if __name__ == "__main__":
    main()
