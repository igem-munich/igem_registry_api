"""Data models for API requests and responses.

Includes:
    FrozenModel: Base model with frozen configuration.
    RestrictedModel: Base model with field restrictions.
    AuditLog: Model for audit log data.
"""

from __future__ import annotations

import logging
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

if TYPE_CHECKING:
    from .license import PartLicense
    from .type import PartType
else:
    PartLicense = Any
    PartType = Any

logger = logging.getLogger(__name__)


__all__ = []


class RestrictedModel(BaseModel):
    """Model with forbidden undeclared fields."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )


class FrozenModel(BaseModel):
    """Model with forbidden undeclared fields."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class ArbitraryModel(BaseModel):
    """Model with arbitrary fields types."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class AuditLog(FrozenModel):
    """Data model for an audit log."""

    created: datetime = Field(
        title="Created",
        description="The ISO 8601 timestamp when the entity was created.",
    )
    updated: datetime = Field(
        title="Updated",
        description="The ISO 8601 timestamp when the entity was last updated.",
    )
