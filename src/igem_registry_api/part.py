"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Self

import requests
from Bio.Seq import Seq
from pydantic import (
    UUID4,
    Field,
    NonNegativeInt,
    field_serializer,
    field_validator,
    model_validator,
)

from .calls import _call, _call_paginated
from .category import Category
from .client import Client
from .license import License
from .schemas import ArbitraryModel, AuditLog
from .type import Type
from .utils import CleanEnum, connected

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class Status(CleanEnum):
    """Part status."""

    DRAFT = "draft"
    SCREENING = "screening"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Part(ArbitraryModel):
    """TODO."""

    client: Client = Field(
        title="Client",
        description="Registry API client instance.",
        default=Client(),
        exclude=True,
        repr=False,
    )

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
    status: Status = Field(
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
    type: Type = Field(
        title="Type",
        description="The type of the part.",
        alias="typeUUID",
    )
    categories: list[Category] = Field(
        title="Categories",
        description="The categories associated with the part.",
        default_factory=list,
        exclude=True,
        repr=False,
    )
    license: License = Field(
        title="License",
        description="The license under which the part is released.",
        alias="licenseUUID",
    )
    source: str = Field(
        title="Source",
        description="The source of the part.",
    )
    sequence: Seq = Field(
        title="Sequence",
        description="The sequence of the part.",
    )
    audit: AuditLog | None = Field(
        title="Audit",
        description="Audit information for the part.",
        default=None,
        exclude=True,
        repr=False,
    )

    @model_validator(mode="before")
    @classmethod
    def extract_type_uuid(cls, data: dict) -> dict:
        """TODO."""
        if (
            "type" in data
            and isinstance(data["type"], dict)
            and "uuid" in data["type"]
        ):
            data["typeUUID"] = data["type"]["uuid"]
            data.pop("type")
        return data

    @field_validator("type", mode="before")
    @classmethod
    def convert_type(cls, value: str) -> Type:
        """TODO."""
        return Type.from_uuid(value)

    @field_validator("categories", mode="before")
    @classmethod
    def convert_categories(cls, value: list[str]) -> list[Category]:
        """TODO."""
        return [Category.from_uuid(uuid) for uuid in value]

    @field_validator("license", mode="before")
    @classmethod
    def convert_license(cls, value: str) -> License:
        """TODO."""
        return License.from_uuid(value)

    @field_validator("sequence", mode="before")
    @classmethod
    def convert_sequence(cls, value: str) -> Seq:
        """TODO."""
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

    @field_serializer("sequence", mode="plain")
    def serialize_sequence(self, value: Seq) -> str:
        """TODO."""
        return str(value)

    @classmethod
    @connected
    def fetch(
        cls,
        client: Client,
        *,
        sort: Literal[
            "uuid",
            "name",
            "slug",
            "status",
            "title",
            "description",
            "type.uuid",
            "type.label",
            "type.slug",
            "licenseUUID",
            "source",
            "sequence",
            "audit.created",
            "audit.updated",
        ] = "audit.created",
        order: Literal["asc", "desc"] = "asc",
        limit: NonNegativeInt | None = None,
        progress: Callable | None = None,
    ) -> list[Self]:
        """TODO."""
        items, _ = _call_paginated(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/parts",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            cls,
            limit=limit,
            progress=progress,
        )
        for item in items:
            item.client = client
        return items

    @classmethod
    @connected
    def search(  # noqa: PLR0913
        cls,
        client: Client,
        search: str,
        *,
        sort: Literal[
            "uuid",
            "name",
            "slug",
            "status",
            "title",
            "description",
            "type.uuid",
            "type.label",
            "type.slug",
            "licenseUUID",
            "source",
            "sequence",
            "audit.created",
            "audit.updated",
        ] = "audit.created",
        order: Literal["asc", "desc"] = "asc",
        limit: NonNegativeInt | None = None,
        progress: Callable | None = None,
    ) -> list[Self]:
        """TODO."""
        items, _ = _call_paginated(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/parts",
                params={
                    "search": search,
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            cls,
            limit=limit,
            progress=progress,
        )
        for item in items:
            item.client = client
        return items

    @classmethod
    @connected
    def get(cls, client: Client, uuid: UUID4 | str) -> Self:
        """TODO."""
        return _call(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/parts/{uuid}",
            ),
            cls,
        )
