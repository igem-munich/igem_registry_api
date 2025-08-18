"""TODO."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal, Self
from uuid import UUID

import requests
from pydantic import (
    UUID4,
    Field,
    HttpUrl,
    NonNegativeInt,
    SkipValidation,
    TypeAdapter,
)

from .calls import call, call_paginated
from .client import Client
from .schemas import ArbitraryModel
from .utils import connected

if TYPE_CHECKING:
    from collections.abc import Callable


class License(ArbitraryModel):
    """TODO."""

    client: SkipValidation[Client] = Field(
        title="Client",
        description="Registry API client instance.",
        default=Client(),
        exclude=True,
        repr=False,
    )

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the license.",
    )
    spdx_id: str = Field(
        title="SPDX ID",
        description="The SPDX identifier for the license.",
        alias="spdxID",
    )
    name: str = Field(
        title="Name",
        description="The name of the license.",
        alias="title",
    )
    description: str = Field(
        title="Description",
        description="A brief description of the license.",
    )
    icon: HttpUrl | None = Field(
        title="Icon",
        description="The URL to the license icon.",
        default=None,
        exclude=True,
        repr=False,
    )
    source: HttpUrl = Field(
        title="Source",
        description="The URL to the license source.",
        alias="url",
    )
    approved: bool = Field(
        title="OSI Approved",
        description="Whether the license is OSI approved.",
        alias="osiApproved",
    )

    @classmethod
    def from_uuid(cls, uuid: str) -> Self:
        """TODO."""
        if uuid in cls.REGISTRY:
            return cls.REGISTRY[uuid]
        raise ValueError

    @classmethod
    @connected
    def fetch(
        cls,
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
        progress: Callable | None = None,
    ) -> list[Self]:
        """TODO."""
        items, _ = call_paginated(
            client,
            requests.Request(
                method="GET",
                url=f"{client.base}/licenses",
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
                url=f"{client.base}/licenses/{uuid}",
            ),
            cls,
        )

    REGISTRY: ClassVar[dict[str, Self]]

    APACHE: ClassVar[Self]
    CC_BY: ClassVar[Self]
    CC_BY_SA: ClassVar[Self]
    CC0: ClassVar[Self]
    GPL: ClassVar[Self]
    MIT: ClassVar[Self]


License.APACHE = License(
    uuid=UUID("bc058bb8-abd9-419a-860e-43b0889cad89"),
    spdxID="apache-2.0",
    title="Apache License 2.0",
    url=TypeAdapter(HttpUrl).validate_python(
        "http://www.apache.org/licenses/LICENSE-2.0",
    ),
    description="A permissive license...",
    osiApproved=True,
)
License.CC_BY = License(
    uuid=UUID("d6c69ca7-8be4-4bc0-b4a8-d3ae1d428aa6"),
    spdxID="cc-by-4.0",
    title="Creative Commons Attribution 4.0 International",
    description=(
        "The Creative Commons Attribution license allows re-distribution "
        "and re-use of a licensed work on the condition that the creator "
        "is appropriately credited."
    ),
    icon=None,
    url=TypeAdapter(HttpUrl).validate_python(
        "https://creativecommons.org/licenses/by/4.0/legalcode",
    ),
    osiApproved=False,
)
License.CC_BY_SA = License(
    uuid=UUID("4e38c689-4c47-456a-9e78-e11caddaa983"),
    spdxID="cc-by-sa-4.0",
    title="Creative Commons Attribution Share Alike 4.0 International",
    description=(
        "Permits almost any use subject to providing credit and license "
        "notice. Frequently used for media assets and educational "
        "materials. The most common license for Open Access scientific "
        "publications."
    ),
    icon=None,
    url=TypeAdapter(HttpUrl).validate_python(
        "https://creativecommons.org/licenses/by-sa/4.0/legalcode",
    ),
    osiApproved=False,
)
License.CC0 = License(
    uuid=UUID("5b2a6fd4-f5fa-4626-a37f-35f1ea89eec7"),
    spdxID="cc0-1.0",
    title="Creative Commons Zero v1.0 Universal",
    description=(
        "CC0 waives copyright interest in a work you've created and "
        "dedicates it to the world-wide public domain. Use CC0 to opt out "
        "of copyright entirely and ensure your work has the widest reach."
    ),
    icon=None,
    url=TypeAdapter(HttpUrl).validate_python(
        "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
    ),
    osiApproved=False,
)
License.GPL = License(
    uuid=UUID("403dfa8a-883c-4e91-892f-ddd2f927f670"),
    spdxID="gpl-3.0-or-later",
    title="GNU General Public License v3.0 or later",
    description=(
        "Permissions of this strong copyleft license are conditioned on "
        "making available complete source code of licensed works and "
        "modifications, which include larger works using a licensed work, "
        "under the same license. Copyright and license notices must be "
        "preserved. Contributors provide an express grant of patent "
        "rights."
    ),
    icon=None,
    url=TypeAdapter(HttpUrl).validate_python(
        "https://www.gnu.org/licenses/gpl-3.0-standalone.html",
    ),
    osiApproved=True,
)
License.MIT = License(
    uuid=UUID("6aeb281a-d268-44da-8bdc-a80e2dce5692"),
    spdxID="mit",
    title="MIT License",
    description=(
        "A short and simple permissive license with conditions only "
        "requiring preservation of copyright and license notices. "
        "Licensed works, modifications, and larger works may be "
        "distributed under different terms and without source code."
    ),
    icon=None,
    url=TypeAdapter(HttpUrl).validate_python(
        "https://opensource.org/licenses/MIT",
    ),
    osiApproved=True,
)

License.REGISTRY = {
    str(item.uuid): item
    for item in [
        License.APACHE,
        License.CC_BY,
        License.CC_BY_SA,
        License.CC0,
        License.GPL,
        License.MIT,
    ]
}
