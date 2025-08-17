"""TODO."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import requests

from .calls import _call_paginated
from .organisations import Organisation
from .types import LicenseData, OrganisationData

if TYPE_CHECKING:
    from pydantic import NonNegativeInt

    from .client import Client


def organisations(
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
) -> list[Organisation]:
    """Fetch a list of organizations."""
    orgs, _ = _call_paginated(
        client,
        requests.Request(
            method="GET",
            url=f"{client.base}/organisations",
            params={
                "orderBy": sort,
                "order": order.upper(),
            },
        ),
        OrganisationData,
        limit=limit,
    )
    return [Organisation.from_data(client, org) for org in orgs]


def licenses(
    client: Client,
    *,
    sort: Literal[
        "uuid",
        "spdxID",
        "title",
        "description",
        "icon",
        "url",
        "osiApproved",
    ] = "title",
    order: Literal["asc", "desc"] = "asc",
    limit: NonNegativeInt | None = None,
) -> list[LicenseData]:
    """Fetch a list of licenses."""
    licenses, _ = _call_paginated(
        client,
        requests.Request(
            method="GET",
            url=f"{client.base}/licenses",
            params={
                "orderBy": sort,
                "order": order.upper(),
            },
        ),
        LicenseData,
        limit=limit,
    )
    return licenses
