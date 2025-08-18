"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import requests
from pydantic import UUID4, Field, NonNegativeInt, PrivateAttr

from .calls import call_paginated
from .client import Client
from .part import Part
from .schemas import ArbitraryModel
from .utils import CleanEnum, authenticated

if TYPE_CHECKING:
    from collections.abc import Callable

    from .organisation import Organisation


logger = logging.getLogger(__name__)


class AccountRoles(CleanEnum):
    """Account roles."""

    ADMIN = "admin"
    USER = "user"


class Account(ArbitraryModel):
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
        description="The unique identifier for the account.",
    )
    role: AccountRoles | None = Field(
        title="Role",
        description="The system role of the account.",
        alias="systemRole",
        default=None,
    )
    first_name: str | None = Field(
        title="First Name",
        description="The first name of the account user.",
        alias="firstName",
        default=None,
    )
    last_name: str | None = Field(
        title="Last Name",
        description="The last name of the account user.",
        alias="lastName",
        default=None,
    )
    photo: str | None = Field(
        title="Photo",
        description="The photo URL of the account.",
        alias="photoURL",
        default=None,
    )
    consent: bool | None = Field(
        title="Consent",
        description=(
            "Whether the account user has opted in to be a contributor."
        ),
        alias="optedIn",
        default=None,
    )

    __username: str | None = PrivateAttr(
        default=None,
    )

    @property
    def username(self) -> str | None:
        """TODO."""
        return self.__username

    def set_username(self, value: str | None) -> None:
        """TODO."""
        object.__setattr__(self, "_Account__username", value)

    @authenticated
    def affiliations(
        self,
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
    ) -> list[Organisation]:
        """Get account affiliations.

        Args:
            sort (Literal[str]): The field to sort the organisations by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of organisations
                to  retrieve.
            progress (Callable | None): A callback function to report progress.

        Returns:
            out (list[Organisation]): Organisations the account belongs to.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .organisation import Organisation  # noqa: PLC0415

        orgs, _ = call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/accounts/{self.uuid}/affiliations",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            Organisation,
            limit=limit,
            progress=progress,
        )
        for org in orgs:
            org.client = self.client
        return orgs

    @authenticated
    def parts(
        self,
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
    ) -> list[Part]:
        """Get parts authored by the account user.

        Args:
            sort (Literal[str]): The field to sort the parts by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of parts to
                retrieve.
            progress (Callable | None): A callback function to report progress.

        Returns:
            out (list[PartData]): The parts authored by the account user.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        parts, _ = call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/parts/accounts/{self.uuid}",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            Part,
            limit=limit,
            progress=progress,
        )
        for part in parts:
            part.client = self.client
        return parts
