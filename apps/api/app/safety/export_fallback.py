"""Write the web app's offline copy of the crisis resources.

The crisis card has to work when the API is unreachable, so the PWA bundles the numbers. This
script regenerates that copy from the reviewed `resources.yaml`; a test fails if they drift.

    uv run python -m app.safety.export_fallback
"""

import json
from pathlib import Path

from app.safety.resources import load_resources

TARGET = (
    Path(__file__).resolve().parents[3] / "web" / "src" / "features" / "crisis" / "fallback.json"
)


def build() -> dict[str, list[dict[str, str | None]]]:
    resources = load_resources().resources
    return {
        locale: [
            {
                "id": r.id,
                "kind": r.kind,
                "name": r.name.get(locale),
                "description": r.description.get(locale),
                "display_number": r.display_number,
                "dial": r.dial,
                "alternate_display_number": r.alternate_display_number,
                "alternate_dial": r.alternate_dial,
            }
            for r in resources
        ]
        for locale in ("en", "ta")
    }


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
