"""ORM models. Every table is registered here so Alembic autogenerate sees it."""

from app.db.base import Base

__all__ = ["Base"]
