"""TODO."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Annotated, Literal, Self
from uuid import UUID

import requests
from Bio.Seq import Seq
from pydantic import (
    UUID4,
    AfterValidator,
    Field,
    NonNegativeInt,
    field_serializer,
    field_validator,
    model_validator,
)

from .author import Author
from .calls import call, call_paginated
from .category import Category
from .client import Client
from .license import License
from .organisation import Organisation
from .schemas import AuditLog, CleanEnum, DynamicModel
from .type import Type
from .utils import authenticated, connected

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class Status(CleanEnum):
    """Part status."""

    DRAFT = "draft"
    SCREENING = "screening"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Reference(DynamicModel):
    """TODO."""

    uuid: Annotated[str, AfterValidator(UUID)] | UUID4 | None = Field(
        title="UUID",
        description="The unique identifier for the part.",
        default=None,
    )

    slug: str | None = Field(
        title="Slug",
        description="The URL-friendly identifier for the part.",
        pattern=r"^bba-[a-z0-9]{1,10}$",
        default=None,
    )

    @model_validator(mode="after")
    def check_input_provided(self) -> Self:
        """TODO."""
        if not self.slug and not self.uuid:
            raise ValueError
        return self


class Part(DynamicModel):
    """TODO."""

    client: Client = Field(
        title="Client",
        description="Registry API client instance.",
        default=Client(),
        exclude=True,
        repr=False,
    )

    uuid: Annotated[str, AfterValidator(UUID)] | UUID4 | None = Field(
        title="UUID",
        description="The unique identifier for the part.",
        default=None,
    )
    id: str | None = Field(
        title="ID",
        description="The identifier for the part.",
        default=None,
        exclude=True,
        repr=False,
    )
    name: str | None = Field(
        title="Name",
        description="The name of the part.",
        pattern=r"^BBa_[A-Z0-9]{1,10}$",
        default=None,
        repr=False,
    )
    slug: str | None = Field(
        title="Slug",
        description="The URL-friendly identifier for the part.",
        pattern=r"^bba-[a-z0-9]{1,10}$",
        default=None,
    )
    status: Status | None = Field(
        title="Status",
        description="The current status of the part.",
        default=None,
    )
    title: str | None = Field(
        title="Title",
        description="The title of the part.",
        default=None,
    )
    description: str | None = Field(
        title="Description",
        description="A brief description of the part.",
        default=None,
    )
    type: Type | None = Field(
        title="Type",
        description="The type of the part.",
        alias="typeUUID",
        default=None,
    )
    categories: Sequence[Category] | None = Field(
        title="Categories",
        description="The categories associated with the part.",
        default_factory=list,
        exclude=True,
        repr=False,
    )
    license: License | None = Field(
        title="License",
        description="The license under which the part is released.",
        alias="licenseUUID",
        default=None,
    )
    source: str | None = Field(
        title="Source",
        description="The source of the part.",
        default=None,
    )
    sequence: Seq | None = Field(
        title="Sequence",
        description="The sequence of the part.",
        default=None,
    )
    audit: AuditLog | None = Field(
        title="Audit",
        description="Audit information for the part.",
        default=None,
        exclude=True,
        repr=False,
    )

    composition: Sequence[Reference | Seq] | Seq | None = Field(
        title="Composition",
        description=(
            "Composition of the part, which can be a list of references or a "
            "raw sequence."
        ),
        default=None,
    )
    authors: Sequence[Author] | None = Field(
        title="Authors",
        description="The authors of the part.",
        default_factory=list,
    )

    @authenticated
    def get_authors(self) -> list[Author]:
        """TODO."""
        items, meta = call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/parts/{self.uuid}/authors",
            ),
            Author,
            list[Organisation],
        )

        orgmap = {org.uuid: org for org in meta}

        for item in items:
            item.account.client = self.client
            item.organisation = orgmap[item.organisation.uuid]
            item.organisation.client = self.client

        return items

    @property
    def is_composite(self) -> bool:
        """Check if the part is composite."""
        return isinstance(self.composition, Sequence)

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

    @field_validator("categories", mode="after")
    @classmethod
    def is_category_unique(
        cls,
        value: Sequence[Category],
    ) -> Sequence[Category]:
        """TODO."""
        if len(value) != len(set(value)):
            raise ValueError
        return value

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
        items, _ = call_paginated(
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
    def search(
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
        items, _ = call_paginated(
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
    def get(cls, client: Client, ref: Reference) -> Self:
        """TODO."""
        if ref.uuid:
            item = call(
                client,
                requests.Request(
                    method="GET",
                    url=f"{client.base}/parts/{ref.uuid}",
                ),
                cls,
            )
        else:
            item = call(
                client,
                requests.Request(
                    method="GET",
                    url=f"{client.base}/parts/slugs/{ref.slug}",
                ),
                cls,
            )
        item.client = client
        return item
