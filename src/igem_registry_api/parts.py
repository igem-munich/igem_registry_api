"""TODO."""

from __future__ import annotations

import logging
from typing import Self

from Bio.Seq import Seq
from pydantic import UUID4, Field, field_validator, model_validator

from .client import Client  # noqa: TC001
from .licenses import License, PartLicense
from .schemas import ArbitraryModel, AuditLog
from .types import PartType, Type
from .utils import CleanEnum

logger = logging.getLogger(__name__)


class PartStatus(CleanEnum):
    """Part status."""

    DRAFT = "draft"
    SCREENING = "screening"
    PUBLISHED = "published"
    REJECTED = "rejected"


class PartData(ArbitraryModel):
    """Data model for part information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the part.",
    )
    id: str | None = Field(
        title="ID",
        description="The identifier for the part.",
        default=None,
        exclude=True,
        repr=False,
    )
    name: str = Field(
        title="Name",
        description="The name of the part.",
        pattern=r"^BBa_[A-Z0-9]{1,10}$",
        repr=False,
    )
    slug: str = Field(
        title="Slug",
        description="The URL-friendly identifier for the part.",
        pattern=r"^bba-[a-z0-9]{1,10}$",
    )
    status: PartStatus = Field(
        title="Status",
        description="The current status of the part.",
    )
    title: str = Field(
        title="Title",
        description="The title of the part.",
    )
    description: str = Field(
        title="Description",
        description="A brief description of the part.",
    )
    type: PartType = Field(
        title="Type",
        description="The type of the part.",
    )
    license: PartLicense = Field(
        title="License",
        description="The license under which the part is released.",
        alias="licenseUUID",
    )
    source: str | None = Field(
        title="Source",
        description="The source of the part.",
        default=None,
    )
    sequence: Seq = Field(
        title="Sequence",
        description="The sequence of the part.",
    )
    audit: AuditLog = Field(
        title="Audit",
        description="Audit information for the part.",
        exclude=True,
        repr=False,
    )

    @model_validator(mode="before")
    @classmethod
    def remove_type_uuid(cls, data: dict) -> dict:
        """Remove the 'typeUUID' key from the input dictionary."""
        if "typeUUID" in data:
            data.pop("typeUUID")
        return data

    @field_validator("license", mode="before")
    @classmethod
    def convert_license(cls, value: str) -> PartLicense:
        """Convert a license UUID to a PartLicense enum member."""
        result = License.from_uuid(value)
        if result is None:
            raise ValueError
        return result

    @field_validator("type", mode="before")
    @classmethod
    def convert_type(cls, value: dict) -> PartType:
        """Convert a type UUID to a PartType enum member."""
        if "uuid" not in value:
            raise ValueError
        result = Type.from_uuid(value["uuid"])
        if result is None:
            raise ValueError
        return result

    @field_validator("sequence", mode="before")
    @classmethod
    def convert_sequence(cls, value: str) -> Seq:
        """Convert a sequence string to a Seq object."""
        return Seq(value)

    @model_validator(mode="after")
    def validate_name_and_slug(self) -> Self:
        """Validate that the slug and name are consistent."""
        if (
            self.slug is not None
            and self.name is not None
            and self.slug != self.name.lower().replace("_", "-")
        ):
            msg = f"Slug '{self.slug}' and name '{self.name}' do not match."
            logger.error(msg)
            raise ValueError(msg)
        return self


class Part(PartData):
    """TODO."""

    client: Client = Field(
        title="Client",
        description="Registry API client instance.",
        exclude=True,
        repr=False,
    )

    @classmethod
    def from_data(
        cls: type[Self],
        client: Client,
        data: PartData,
    ) -> Self:
        """Create a Part instance from PartData."""
        payload = data.model_dump(by_alias=True)
        return cls.model_validate({**payload, "client": client})
