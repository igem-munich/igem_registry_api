"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

import requests
from pydantic import ConfigDict, Field, SkipValidation

from .calls import _call, _call_paginated
from .types import AccountData, OrganisationData
from .utils import authenticated

if TYPE_CHECKING:
    from .accounts import Account
    from .client import Client
else:
    Client = Any

logger = logging.getLogger(__name__)


class Organisation(OrganisationData):
    """TODO."""

    client: SkipValidation[Client] = Field(
        title="Client",
        description="Registry API client instance.",
        exclude=True,
        repr=False,
    )

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
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
    def members(self) -> list[Account]:
        """Get a list of members in the organisation.

        Returns:
            list[Account]: A list of accounts that are members of the
                organisation.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .accounts import Account  # noqa: PLC0415

        users, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/organisations/{self.uuid}/members",
            ),
            AccountData,
        )
        return [Account.from_data(self.client, user) for user in users]
