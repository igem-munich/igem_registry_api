"""TODO."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal, Self

import requests
from pydantic import UUID4, Field, NonNegativeInt, PrivateAttr

from .calls import _call_paginated
from .client import Client  # noqa: TC001
from .part import Part, PartData
from .schemas import ArbitraryModel
from .utils import CleanEnum, authenticated

if TYPE_CHECKING:
    from .organisation import Organisation


logger = logging.getLogger(__name__)


class AccountRoles(CleanEnum):
    """Account roles."""

    ADMIN = "admin"
    USER = "user"


class AccountData(ArbitraryModel):
    """Data model for account information."""

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


class Account(AccountData):
    """TODO."""

    client: Client = Field(
        title="Client",
        description="Registry API client instance.",
        exclude=True,
        repr=False,
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
    ) -> list[Organisation]:
        """Get account affiliations.

        Args:
            sort (Literal[str]): The field to sort the organisations by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of organisations
                to  retrieve.

        Returns:
            out (list[OrganisationData]): Organisations the account belongs to.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        from .organisation import (  # noqa: PLC0415
            Organisation,
            OrganisationData,
        )

        orgs, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/accounts/{self.uuid}/affiliations",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            OrganisationData,
            limit=limit,
        )
        return [Organisation.from_data(self.client, org) for org in orgs]

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
    ) -> list[Part]:
        """Get parts authored by the account user.

        Args:
            sort (Literal[str]): The field to sort the parts by.
            order (Literal[str]): The order of sorting, either 'asc' or 'desc'.
            limit (NonNegativeInt | None): The maximum number of parts to
                retrieve.

        Returns:
            out (list[PartData]): The parts authored by the account user.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        parts, _ = _call_paginated(
            self.client,
            requests.Request(
                method="GET",
                url=f"{self.client.base}/parts/accounts/{self.uuid}",
                params={
                    "orderBy": sort,
                    "order": order.upper(),
                },
            ),
            PartData,
            limit=limit,
        )
        return [Part.from_data(self.client, part) for part in parts]
