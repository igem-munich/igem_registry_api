"""Data models for API requests and responses.

Includes:
    ClientMode: API client operation modes.
    ClosedModel: Model with forbidden undeclared fields.
    HealthCheck: Health check model for the registry instance.
    ResourceData: Data model for registry resources.
    ServerInfo: Data model for backend server information.
    StatusItem: Data model for resource status.
    AuditLog: Data model for audit logs.
    UserData: Data model for user information.
    OrganisationType: Organisation types.
    OrganisationData: Data model for organization information.
    partial: Create a partial model from the original model.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Self

from Bio.Seq import Seq
from pydantic import (
    UUID4,
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    NonNegativeInt,
    model_validator,
)

logger = logging.getLogger(__name__)


__all__ = [
    "ClientMode",
    "ClosedModel",
    "HealthCheck",
    "OrganisationData",
]


class ClosedModel(BaseModel):
    """Model with forbidden undeclared fields."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ClientMode(Enum):
    """API client operation modes."""

    NONE = "NONE"
    ANON = "ANON"
    AUTH = "AUTH"


class StatusItem(ClosedModel):
    """Data model for resource status."""

    status: Literal["up", "down"] = Field(
        title="Status",
        description="The status of the resource.",
    )


class ServerInfo(StatusItem):
    """Data model for backend server information."""

    environment: Literal["production", "staging", "development"] = Field(
        title="Environment",
        description="The environment in which the server is running.",
    )
    version: str = Field(
        title="Version",
        description="The version of the server.",
    )


class ResourceData(ClosedModel):
    """Data model for registry resources."""

    server: ServerInfo | None = Field(
        title="Server",
        description="Data about the server status.",
        default=None,
    )
    database: StatusItem | None = Field(
        title="Database",
        description="Data about the database status.",
        default=None,
    )
    memory_rss: StatusItem | None = Field(
        title="Memory RSS",
        description="Data about the memory RSS status.",
        default=None,
    )
    redis: StatusItem | None = Field(
        title="Redis",
        description="Data about the Redis status.",
        default=None,
    )


class HealthCheck(ClosedModel):
    """Health check model for the registry instance."""

    status: Literal["ok", "error"] = Field(
        title="Status",
        description="Registry instance health status.",
    )
    info: ResourceData = Field(
        title="Info",
        description="Information about the registry instance resources.",
    )
    error: ResourceData = Field(
        title="Error",
        description="Errors encountered by the registry instance resources.",
    )
    details: ResourceData = Field(
        title="Details",
        description="Further details about the registry instance resources.",
    )


class AuditLog(ClosedModel):
    """Data model for an audit log."""

    created: datetime = Field(
        title="Created",
        description="The ISO 8601 timestamp when the entity was created.",
    )
    updated: datetime = Field(
        title="Updated",
        description="The ISO 8601 timestamp when the entity was last updated.",
    )


class AccountRoles(Enum):
    """Account roles."""

    ADMIN = "admin"
    USER = "user"


class OrganisationType(Enum):
    """Organisation types."""

    EDUCATION = "education"
    COMPANY = "company"
    NON_PROFIT = "non-profit"
    GOVERNMENT = "government"
    IGEM_TEAM = "igem-team"
    OTHER = "other"


class OrganisationData(ClosedModel):
    """Data model for organisation information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the organisation.",
    )
    name: str = Field(
        title="Name",
        description="The name of the organisation.",
    )
    type: OrganisationType = Field(
        title="Type",
        description="The type of the organisation.",
    )
    link: HttpUrl = Field(
        title="Link",
        description="The link to the organisation's website.",
    )
    audit: AuditLog = Field(
        title="Audit",
        description="Audit information for the organisation.",
        exclude=True,
        repr=False,
    )


class PartStatus(Enum):
    """Part status."""

    DRAFT = "draft"
    SCREENING = "screening"
    PUBLISHED = "published"
    REJECTED = "rejected"


class PartType(Enum):
    """Part types objects."""

    TERMINATOR = "828126a4-2ae9-47ce-9079-42ad82a62d32"
    RBS = "9136e5fb-7232-4992-b828-d4fa4889ce63"
    DNA = "b252b723-460a-4b72-8eb0-de389932de00"
    CODING = "a797873a-d73a-454d-9c03-ee5dd5974980"
    REPORTER = "0a6e2d17-78fd-42f3-836c-181d545cfe27"
    REGULATORY = "324e9810-8719-4dd8-8c39-989a015a96a1"
    RNA = "258808a8-f859-4f0f-a1b9-17e591020eb8"
    GENERATOR = "4a83aa73-05f2-4c21-8b0f-80e325daceda"
    INVERTER = "0eb9e8c5-5e40-4bdf-a405-cbcd69e50e7d"
    INTERMEDIATE = "28abb4c8-7237-462c-a904-bb722692e0ff"
    SIGNALLING = "c0495fda-9566-42c7-b9e8-75a04f53dbd3"
    MEASUREMENT = "495a25e5-f788-4bd2-899c-2f4b3e503525"
    TRANSLATIONAL_UNIT = "a5e00389-c83b-410d-adee-048df3ecaf84"
    PLASMID_BACKBONE = "6c416322-36f4-4348-8ebc-3ee82622a000"
    PRIMER = "e4bfbdbc-c096-4dfb-aae2-634204149ef2"
    CELL = "c27b7035-c0b7-4d78-a90f-89dfdae571e6"
    DEVICE = "6c8acd81-d083-4f0c-9601-181ef22497d9"
    PLASMID = "8ac2d621-12cf-4aec-9b88-a78250438517"
    CONJUGATION = "5b12b3f8-a959-4503-9e62-40a4bd38626a"
    T7 = "2fabb627-e479-45b1-853d-623edf20802c"


class PartLicense(Enum):
    """Part licenses."""

    APACHE = "bc058bb8-abd9-419a-860e-43b0889cad89"
    CC_BY = "d6c69ca7-8be4-4bc0-b4a8-d3ae1d428aa6"
    CC_BY_SA = "4e38c689-4c47-456a-9e78-e11caddaa983"
    CC0 = "5b2a6fd4-f5fa-4626-a37f-35f1ea89eec7"
    GPL = "403dfaa8-883c-4e91-892f-ddd2f927f670"
    MIT = "6aeb281a-d268-44da-8bdc-a80e2dce5692"


class PartData(ClosedModel):
    """Data model for part information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the part.",
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
        alias="typeUUID",
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
    sequence: Annotated[
        str,
        AfterValidator(lambda seq: Seq(seq)),
    ] = Field(
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
    def remove_type_object(cls, data: Any) -> Any:
        if isinstance(data, dict) and "type" in data:
            del data["type"]
        return data

    @model_validator(mode="before")
    @classmethod
    def remove_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" in data:
            del data["id"]
        return data

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


class RateLimit(ClosedModel):
    """Rate limit information model for API requests."""

    balance: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Balance",
        description=(
            "Remaining requests for short, medium, and large call windows"
        ),
        default=(0, 0, 0),
        alias="remaining",
    )
    reset: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Reset",
        description=(
            "Reset times (seconds) for short, medium, and large call windows"
        ),
        default=(5, 60, 600),
        alias="reset",
    )
    quota: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Quota",
        description=(
            "Request limits for short, medium, and large call windows"
        ),
        default=(5, 60, 200),
        alias="limit",
    )


class PaginatedResponse[
    ResponseObject: ClosedModel,
    MetadataObject: ClosedModel | None,
](
    ClosedModel,
):
    """Generic model for API responses that return paginated data.

    This model wraps a list of response objects together with the current page
    number, the total number of available objects, and optional metadata
    provided by the API.
    """

    data: list[ResponseObject] = Field(
        title="Data",
        description="A list of data objects returned in the response.",
        min_length=0,
        max_length=100,
    )
    page: int = Field(
        title="Page",
        description="The current page number.",
        ge=1,
    )
    total: int = Field(
        title="Total",
        description="The total number of objects available.",
        ge=0,
    )
    metadata: MetadataObject | None = Field(
        title="Metadata",
        description="Additional metadata about the response.",
        default=None,
    )
