"""TODO."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import requests

from .calls import _call_paginated
from .category import Category, CategoryData
from .license import License, LicenseData
from .organisation import Organisation, OrganisationData
from .part import Part, PartData
from .type import Type, TypeData

if TYPE_CHECKING:
    from collections.abc import Callable

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
) -> list[License]:
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
    return [License.from_data(lic) for lic in licenses]


def types(
    client: Client,
    *,
    sort: Literal[
        "uuid",
        "label",
        "slug",
    ] = "label",
    order: Literal["asc", "desc"] = "asc",
    limit: NonNegativeInt | None = None,
) -> list[Type]:
    """Fetch a list of part types."""
    types, _ = _call_paginated(
        client,
        requests.Request(
            method="GET",
            url=f"{client.base}/parts/types",
            params={
                "orderBy": sort,
                "order": order.upper(),
            },
        ),
        TypeData,
        limit=limit,
    )
    return [Type.from_data(ptype) for ptype in types]


def categories(
    client: Client,
    *,
    sort: Literal[
        "uuid",
        "label",
        "value",
        "description",
    ] = "label",
    order: Literal["asc", "desc"] = "asc",
    limit: NonNegativeInt | None = None,
) -> list[Category]:
    """Fetch a list of part categories."""
    categories, _ = _call_paginated(
        client,
        requests.Request(
            method="GET",
            url=f"{client.base}/parts/categories",
            params={
                "orderBy": sort,
                "order": order.upper(),
            },
        ),
        CategoryData,
        limit=limit,
    )
    return [Category.from_data(cat) for cat in categories]


def parts(
    client: Client,
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
    """Fetch a list of parts."""
    parts, _ = _call_paginated(
        client,
        requests.Request(
            method="GET",
            url=f"{client.base}/parts",
            params={
                "orderBy": sort,
                "order": order.upper(),
            },
        ),
        PartData,
        limit=limit,
        progress=progress,
    )
    return [Part.from_data(client, part) for part in parts]
