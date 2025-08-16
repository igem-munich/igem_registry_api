"""Data models for API requests and responses.

Includes:
    ClientMode: API client operation modes.
    ClosedModel: Model with forbidden undeclared fields.
    HealthCheck: Health check model for the registry instance.
    PartialResourceData: Partial data model for registry resources.
    ResourceData: Data model for registry resources.
    ServerInfo: Data model for backend server information.
    StatusItem: Data model for resource status.
    UserData: Data model for user information.
    partial: Create a partial model from the original model.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    create_model,
)

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


__all__ = [
    "ClientMode",
    "ClosedModel",
    "HealthCheck",
    "UserData",
    "partial",
]


def partial[Partial: BaseModel](model: type[Partial]) -> type[Partial]:
    """Create a partial model from the original model.

    This function creates a new Pydantic model that has the same fields as the
    original model, but all fields are optional.

    Attributes:
        model (BaseModel): The original model to create a partial model from.

    """

    def optional(
        field: FieldInfo,
        default: Any = None,
    ) -> tuple[Any, FieldInfo]:
        clone = deepcopy(field)
        clone.default = default
        clone.annotation = field.annotation or None
        return clone.annotation, clone

    return create_model(
        model.__name__,
        __base__=model,
        __module__=model.__module__,
        __config__=None,
        __doc__=None,
        __validators__=None,
        __cls_kwargs__=None,
        **{name: optional(info) for name, info in model.model_fields.items()},
    )


class ClosedModel(BaseModel):
    """Model with forbidden undeclared fields."""

    model_config = ConfigDict(extra="forbid")


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

    server: ServerInfo = Field(
        title="Server",
        description="Data about the server status.",
    )
    database: StatusItem = Field(
        title="Database",
        description="Data about the database status.",
    )
    memory_rss: StatusItem = Field(
        title="Memory RSS",
        description="Data about the memory RSS status.",
    )
    redis: StatusItem = Field(
        title="Redis",
        description="Data about the Redis status.",
    )


@partial
class PartialResourceData(ResourceData):
    """Partial data model for registry resources."""


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
    error: PartialResourceData = Field(
        title="Error",
        description="Errors encountered by the registry instance resources.",
    )
    details: ResourceData = Field(
        title="Details",
        description="Further details about the registry instance resources.",
    )


class UserData(ClosedModel):
    """User data model for authenticated users."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the user.",
    )
    role: Literal["admin", "user"] = Field(
        title="Role",
        description="The system role of the user.",
        alias="systemRole",
    )
    first_name: str = Field(
        title="First Name",
        description="The first name of the user.",
        alias="firstName",
    )
    last_name: str = Field(
        title="Last Name",
        description="The last name of the user.",
        alias="lastName",
    )
    photo: str | None = Field(
        title="Photo",
        description="The photo URL of the user.",
        alias="photoURL",
        default=None,
    )
    consent: bool = Field(
        title="Consent",
        description="Whether the user has opted in to be a contributor.",
        alias="optedIn",
    )


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
