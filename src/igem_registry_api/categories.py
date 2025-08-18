"""TODO."""

from __future__ import annotations

from uuid import UUID

from pydantic import UUID4, Field

from .schemas import FrozenModel
from .utils import CleanEnum


class CategoryData(FrozenModel):
    """Data model for part category information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the part category.",
    )
    label: str | None = Field(
        title="Label",
        description="The label of the part category.",
        alias="value",
        default=None,
    )
    description: str | None = Field(
        title="Description",
        description="A brief description of the part category.",
        default=None,
    )


class Category(CategoryData):
    """TODO."""

    @classmethod
    def from_data(cls, data: CategoryData) -> Category:
        """TODO."""
        return cls(**data.model_dump())

    @classmethod
    def from_uuid(cls, uuid: str) -> PartCategory | None:
        """TODO."""
        for item in PartCategory:
            if item.value.uuid == UUID(uuid):
                return item
        return None

    @classmethod
    def from_label(cls, label: str) -> PartCategory | None:
        """TODO."""
        for item in PartCategory:
            if item.value.label == label:
                return item
        return None


class PartCategory(CleanEnum):
    """TODO."""
