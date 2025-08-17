"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

import requests
from pydantic import ConfigDict, Field, PrivateAttr, SkipValidation

from .calls import _call_paginated
from .types import AccountData, OrganisationData, PartData
from .utils import authenticated

if TYPE_CHECKING:
    from .client import Client
    from .organisations import Organisation
else:
    Client = Any


logger = logging.getLogger(__name__)


class Account(AccountData):
    """TODO."""

    client: SkipValidation[Client] = Field(
        title="Client",
        description="Registry API client instance.",
        exclude=True,
        repr=False,
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

    @classmethod
    def from_data(
        cls: type[Self],
        client: Client,
        data: AccountData,
    ) -> Self:
        """TODO."""
        payload = data.model_dump(by_alias=True)
        return cls.model_validate({**payload, "client": client})

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
    def affiliations(self) -> list[Organisation]:
        """Get account affiliations.

        Returns:
            out (list[OrganisationData]): Organisations the account belongs to.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .organisations import Organisation  # noqa: PLC0415

        orgs, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/accounts/{self.uuid}/affiliations",
            ),
            OrganisationData,
        )
        return [Organisation.from_data(self.client, org) for org in orgs]

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
