"""Crisis resources, loaded once from the human-reviewed `resources.yaml`."""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, HttpUrl

RESOURCES_FILE = Path(__file__).with_name("resources.yaml")
MAX_AGE_DAYS = 180

Locale = Literal["en", "ta"]


class Localised(BaseModel):
    en: str
    ta: str

    def get(self, locale: Locale) -> str:
        return self.ta if locale == "ta" else self.en


class Resource(BaseModel):
    id: str
    kind: Literal["helpline", "emergency"]
    name: Localised
    display_number: str
    dial: str
    alternate_display_number: str | None = None
    alternate_dial: str | None = None
    description: Localised
    hours: str
    cost: Literal["free", "paid"]
    verified_against: list[HttpUrl]
    last_verified: date


class ResourceFile(BaseModel):
    version: int
    resources: list[Resource]


class ResourceOut(BaseModel):
    id: str
    kind: Literal["helpline", "emergency"]
    name: str
    description: str
    display_number: str
    dial: str
    alternate_display_number: str | None
    alternate_dial: str | None
    hours: str
    cost: Literal["free", "paid"]
    last_verified: date


@lru_cache
def load_resources() -> ResourceFile:
    raw = yaml.safe_load(RESOURCES_FILE.read_text(encoding="utf-8"))
    return ResourceFile.model_validate(raw)


def localised_resources(locale: Locale) -> list[ResourceOut]:
    return [
        ResourceOut(
            id=r.id,
            kind=r.kind,
            name=r.name.get(locale),
            description=r.description.get(locale),
            display_number=r.display_number,
            dial=r.dial,
            alternate_display_number=r.alternate_display_number,
            alternate_dial=r.alternate_dial,
            hours=r.hours,
            cost=r.cost,
            last_verified=r.last_verified,
        )
        for r in load_resources().resources
    ]


def resource_ids() -> list[str]:
    return [r.id for r in load_resources().resources]
