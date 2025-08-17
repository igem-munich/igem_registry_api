"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self

import requests
from pydantic import UUID4, ConfigDict, Field, PrivateAttr

from .calls import _call_paginated
from .types import AccountRoles, ClosedModel, OrganisationData, PartData
from .utils import authenticated

if TYPE_CHECKING:
    from .client import Client


logger = logging.getLogger(__name__)


class Account(ClosedModel):
    """TODO."""

    client: Client = Field(
        title="Client",
        description="Registry API client instance.",
        exclude=True,
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

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    @property
    def username(self) -> str | None:
        """TODO."""
        return self.__username

    def set_username(self, value: str | None) -> None:
        """TODO."""
        object.__setattr__(self, "_Account__username", value)

    @authenticated
    def info(self) -> Self:
        """Get account information.

        Returns:
            out (Account): The account information.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        msg = (
            "Retrieval of registry account details for entities other than "
            "the authenticated account user is not supported by the API."
        )
        logger.error(msg)
        raise NotImplementedError(msg)
        return self

    @authenticated
    def affiliations(self) -> list[OrganisationData]:
        """Get account affiliations.

        Returns:
            out (list[OrganisationData]): Organisations the account belongs to.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        organisations, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/accounts/{self.uuid}/affiliations",
            ),
            OrganisationData,
        )
        return organisations

    @authenticated
    def parts(self) -> list[PartData]:
        """Get user parts."""
        parts, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/parts/accounts/{self.uuid}",
            ),
            PartData,
        )
        return parts
