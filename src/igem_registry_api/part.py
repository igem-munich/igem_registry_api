"""TODO."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import UUID

import requests
from Bio.Seq import Seq
from pydantic import (
    UUID4,
    Field,
    NonNegativeInt,
    SkipValidation,
    field_serializer,
    field_validator,
    model_validator,
)

from .annotation import Annotation
from .author import Author
from .calls import call, call_paginated
from .category import Category
from .client import Client
from .errors import InputValidationError
from .license import License
from .organisation import Organisation
from .schemas import AuditLog, CleanEnum, DynamicModel
from .type import Type
from .utils import connected

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Self

logger = logging.getLogger(__name__)


class Status(CleanEnum):
    """Part status."""

    DRAFT = "draft"
    SCREENING = "screening"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Reference(DynamicModel):
    """Reference to a Registry part.

    Represents a reference to a part, identified by either its UUID or slug.
    At least one identifier must be provided. Can be used to fetch the full
    part details from the Registry using the `Part.get` method.

    Attributes:
        uuid (str | UUID4 | None): Unique identifier for the part.
        slug (str | None): URL-friendly identifier for the part.

    Examples:
        Creating references by UUID or slug, and fetching the corresponding
        part:

        ```python
        from igem_registry_api import Client, Part, Reference

        ref_by_uuid = Reference(uuid="123e4567-e89b-12d3-a456-426614174000")
        ref_by_slug = Reference(slug="bba-0000000001")

        Part.get(client, ref_by_uuid)
        Part.get(client, ref_by_slug)
        ```

    """

    uuid: Annotated[
        str | UUID4 | None,
        Field(
            title="UUID",
            description="Unique identifier for the part.",
            frozen=True,
        ),
    ] = None

    slug: Annotated[
        str | None,
        Field(
            title="Slug",
            description="The URL-friendly identifier for the part.",
            pattern=r"^bba-[a-z0-9]{1,10}$",
            frozen=True,
        ),
    ] = None

    @field_validator("uuid", mode="after")
    @classmethod
    def ensure_uuid(cls, value: str | UUID4) -> UUID4:
        """Normalize the part UUID to a UUID4 instance.

        Accepts both `str` and `UUID4` objects for usability, while ensuring
        the stored value is always a `UUID4`. This avoids type checking errors
        when a `str` input is provided.

        Args:
            value (str | UUID4): Unique part identifier.

        Returns:
            out (UUID4): A validated version-4 UUID object.

        Raises:
            InputValidationError: If the input value is not a valid UUID4.

        """
        if isinstance(value, str):
            try:
                value = UUID(value, version=4)
            except Exception as e:
                raise InputValidationError(error=e) from e
        return value

    @model_validator(mode="after")
    def check_input_provided(self) -> Self:
        """Ensure that at least one identifier is provided.

        Raises:
            InputValidationError: If neither `slug` nor `uuid` is provided.

        """
        if not self.slug and not self.uuid:
            message = "Either slug or uuid must be provided."
            e = ValueError(message)
            raise InputValidationError(error=e) from e
        return self


class Part(DynamicModel):
    """TODO."""

    client: Annotated[
        SkipValidation[Client],
        Field(
            title="Client",
            description="Registry API client.",
            frozen=False,
            exclude=True,
            repr=False,
        ),
    ] = Field(default_factory=Client.stub)

    uuid: Annotated[
        str | UUID4 | None,
        Field(
            title="UUID",
            description="Unique identifier for the part.",
            frozen=True,
        ),
    ] = None
    id: Annotated[
        str | None,
        Field(
            title="ID",
            description="The identifier for the part.",
            frozen=True,
            exclude=True,
            repr=False,
        ),
    ] = None
    slug: Annotated[
        str | None,
        Field(
            title="Slug",
            description="The URL-friendly identifier for the part.",
            pattern=r"^bba-[a-z0-9]{1,10}$",
            frozen=True,
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            title="Name",
            description="The name of the part.",
            pattern=r"^BBa_[A-Z0-9]{1,10}$",
            frozen=True,
            repr=False,
        ),
    ] = None
    status: Annotated[
        Status | None,
        Field(
            title="Status",
            description="The current status of the part.",
            frozen=True,
        ),
    ] = None

    title: Annotated[
        str | None,
        Field(
            title="Title",
            description="The title of the part.",
            min_length=3,
            max_length=100,
            frozen=False,
        ),
    ] = None
    source: Annotated[
        str | None,
        Field(
            title="Source",
            description="The source of the part.",
            max_length=250,
            frozen=False,
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            title="Description",
            description="A brief description of the part.",
            frozen=False,
        ),
    ] = None
    type: Annotated[
        Type | None,
        Field(
            title="Type",
            description="The type of the part.",
            alias="typeUUID",
            frozen=False,
        ),
    ] = None
    categories: Annotated[
        Sequence[Category] | None,
        Field(
            title="Categories",
            description="The categories associated with the part.",
            frozen=False,
            exclude=True,
            repr=False,
        ),
    ] = Field(default_factory=list)
    license: Annotated[
        License | None,
        Field(
            title="License",
            description="The license under which the part is released.",
            alias="licenseUUID",
            frozen=False,
        ),
    ] = None
    sequence: Annotated[
        Seq | None,
        Field(
            title="Sequence",
            description="The sequence of the part.",
            frozen=True,
        ),
    ] = None
    deleted: Annotated[
        datetime | None,
        Field(
            title="Deleted",
            description="The deletion timestamp of the part, if applicable.",
            alias="deletedAt",
            frozen=True,
            exclude=True,
            repr=False,
        ),
    ] = None
    audit: Annotated[
        AuditLog | None,
        Field(
            title="Audit",
            description="Audit information for the part.",
            frozen=True,
            exclude=True,
            repr=False,
        ),
    ] = None

    composition: Annotated[
        Sequence[Reference | Seq] | Seq | None,
        Field(
            title="Composition",
            description=(
                "Composition of the part, which can be a list of references "
                "or a raw sequence."
            ),
            frozen=False,
        ),
    ] = None
    authors: Annotated[
        Sequence[Author] | None,
        Field(
            title="Authors",
            description="The authors of the part.",
            frozen=False,
        ),
    ] = Field(default_factory=list)
    annotations: Annotated[
        Sequence[Annotation] | None,
        Field(
            title="Annotations",
            description="The sequence annotations of the part.",
            frozen=False,
        ),
    ] = Field(default_factory=list)

    @property
    def is_composite(self) -> bool:
        """Check if the part is composite.

        A part is considered composite if its composition is defined and
        contains at least one `Reference` object.

        Returns:
            out (bool): `True` if the part is composite, `False` otherwise.

        """
        if isinstance(self.composition, Sequence):
            return any(isinstance(x, Reference) for x in self.composition)
        return False

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

    @field_validator("uuid", mode="after")
    @classmethod
    def ensure_uuid(cls, value: str | UUID4) -> UUID4:
        """Normalize the part UUID to a UUID4 instance.

        Accepts both `str` and `UUID4` objects for usability, while ensuring
        the stored value is always a `UUID4`. This avoids type checking errors
        when a `str` input is provided.

        Args:
            value (str | UUID4): Unique part identifier.

        Returns:
            out (UUID4): A validated version-4 UUID object.

        Raises:
            InputValidationError: If the input value is not a valid UUID4.

        """
        if isinstance(value, str):
            try:
                value = UUID(value, version=4)
            except Exception as e:
                raise InputValidationError(error=e) from e
        return value

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

    @connected
    def load_authors(self) -> list[Author]:
        """Load authors of the part.

        Returns:
            out (list[Author]): List of associated authors.

        Raises:
            NotConnectedError: If the client is in offline mode.

        """
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

        self.authors = items
        return items

    @connected
    def load_annotations(self) -> list[Annotation]:
        """Load annotations of the part.

        Returns:
            out (list[Annotation]): List of sequence annotations.

        Raises:
            NotConnectedError: If the client is in offline mode.

        """
        items, _ = call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/parts/{self.uuid}/sequence-features",
            ),
            Annotation,
        )

        self.annotations = items
        return items

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
        elif ref.slug:
            item = call(
                client,
                requests.Request(
                    method="GET",
                    url=f"{client.base}/parts/slugs/{ref.slug}",
                ),
                cls,
            )
        else:
            message = "Incomplete reference, missing slug or uuid."
            e = ValueError(message)
            raise InputValidationError(error=e) from e
        item.client = client
        return item
