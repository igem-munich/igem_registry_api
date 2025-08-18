"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Self

import requests
from pydantic import UUID4, Field, HttpUrl, NonNegativeInt

from .calls import _call, _call_paginated
from .client import Client  # noqa: TC001
from .schemas import ArbitraryModel, AuditLog
from .utils import CleanEnum, authenticated

if TYPE_CHECKING:
    from .account import Account

logger = logging.getLogger(__name__)


class OrganisationType(CleanEnum):
    """Organisation types."""

    EDUCATION = "education"
    COMPANY = "company"
    NON_PROFIT = "non-profit"
    GOVERNMENT = "government"
    IGEM_TEAM = "igem-team"
    OTHER = "other"


class OrganisationData(ArbitraryModel):
    """Data model for organization information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the organisation.",
    )
    name: str | None = Field(
        title="Name",
        description="The name of the organisation.",
        default=None,
    )
    type: OrganisationType | None = Field(
        title="Type",
        description="The type of the organisation.",
        default=None,
    )
    link: HttpUrl | None = Field(
        title="Link",
        description="The link to the organisation's website.",
        default=None,
    )
    audit: AuditLog | None = Field(
        title="Audit",
        description="Audit information for the organisation.",
        default=None,
        exclude=True,
        repr=False,
    )


class Organisation(OrganisationData):
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
        data: OrganisationData,
    ) -> Self:
        """TODO."""
        payload = data.model_dump(by_alias=True)
        return cls.model_validate({**payload, "client": client})

    @authenticated
    def info(self) -> Organisation:
        """Get account information.

        Returns:
            out (Account): The account information.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        return _call(
            self.client,
            requests.Request(
                method="GET",
                url=f"/organisations/{self.uuid}",
            ),
            Organisation,
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
    ) -> list[Account]:
        """Get a list of members in the organisation.

        Args:
            sort (Literal[str]): The field to sort the members by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of members to
                retrieve.

        Returns:
            out (list[Account]): A list of accounts that are members of the
                organisation.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .account import Account, AccountData  # noqa: PLC0415

        users, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/organisations/{self.uuid}/members",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            AccountData,
            limit=limit,
        )
        return [Account.from_data(self.client, user) for user in users]
