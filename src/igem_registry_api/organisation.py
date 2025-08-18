"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Self

import requests
from pydantic import UUID4, Field, HttpUrl, NonNegativeInt

from .calls import call, call_paginated
from .client import Client
from .schemas import ArbitraryModel, AuditLog
from .utils import CleanEnum, authenticated, connected

if TYPE_CHECKING:
    from collections.abc import Callable

    from .account import Account

logger = logging.getLogger(__name__)


class Kind(CleanEnum):
    """Organisation kind."""

    EDUCATION = "education"
    COMPANY = "company"
    NON_PROFIT = "non-profit"
    GOVERNMENT = "government"
    IGEM_TEAM = "igem-team"
    OTHER = "other"


class Organisation(ArbitraryModel):
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
        description="The unique identifier for the organisation.",
    )
    name: str = Field(
        title="Name",
        description="The name of the organisation.",
    )
    kind: Kind = Field(
        title="Kind",
        description="The kind of the organisation.",
        alias="type",
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

    @authenticated
    def members(
        self,
        *,
        sort: Literal[
            "uuid",
            "firstName",
            "lastName",
            "systemRole",
            "photoURL",
        ] = "firstName",
        order: Literal["asc", "desc"] = "asc",
        limit: NonNegativeInt | None = None,
        progress: Callable | None = None,
    ) -> list[Account]:
        """Get a list of members in the organisation.

        Args:
            sort (Literal[str]): The field to sort the members by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of members to
                retrieve.
            progress (Callable | None): A callback function to report progress.

        Returns:
            out (list[Account]): A list of accounts that are members of the
                organisation.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .account import Account  # noqa: PLC0415

        users, _ = call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/organisations/{self.uuid}/members",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            Account,
            limit=limit,
            progress=progress,
        )
        for user in users:
            user.client = self.client

        return users

    @classmethod
    @connected
    def fetch(
        cls,
        client: Client,
        *,
        sort: Literal[
            "uuid",
            "name",
            "type",
            "link",
            "audit.created",
            "audit.updated",
        ] = "name",
        order: Literal["asc", "desc"] = "asc",
        limit: NonNegativeInt | None = None,
        progress: Callable | None = None,
    ) -> list[Self]:
        """TODO."""
        items, _ = call_paginated(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/organisations",
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
    def get(cls, client: Client, uuid: UUID4 | str) -> Self:
        """TODO."""
        return call(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/organisations/{uuid}",
            ),
            cls,
        )
