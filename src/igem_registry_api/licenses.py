"""TODO."""

from __future__ import annotations

from uuid import UUID

from pydantic import UUID4, Field, HttpUrl, TypeAdapter

from .schemas import FrozenModel
from .utils import CleanEnum


class LicenseData(FrozenModel):
    """Data model for license information."""

    uuid: UUID4 = Field(
        title="UUID",
        description="The unique identifier for the license.",
    )
    spdx_id: str | None = Field(
        title="SPDX ID",
        description="The SPDX identifier for the license.",
        alias="spdxID",
        default=None,
    )
    name: str | None = Field(
        title="Name",
        description="The name of the license.",
        alias="title",
        default=None,
    )
    description: str | None = Field(
        title="Description",
        description="A brief description of the license.",
        default=None,
    )
    icon: HttpUrl | None = Field(
        title="Icon",
        description="The URL to the license icon.",
        default=None,
    )
    source: HttpUrl | None = Field(
        title="Source",
        description="The URL to the license source.",
        alias="url",
        default=None,
    )
    approved: bool | None = Field(
        title="OSI Approved",
        description="Whether the license is OSI approved.",
        alias="osiApproved",
        default=None,
    )


class License(LicenseData):
    """TODO."""

    @classmethod
    def from_data(cls, data: LicenseData) -> License:
        """TODO."""
        return cls(**data.model_dump())

    @classmethod
    def from_uuid(cls, uuid: str) -> PartLicense | None:
        """TODO."""
        for item in PartLicense:
            if item.value.uuid == UUID(uuid):
                return item
        return None

    @classmethod
    def from_spdx_id(cls, spdx_id: str) -> PartLicense | None:
        """TODO."""
        for item in PartLicense:
            if item.value.spdx_id == spdx_id:
                return item
        return None


class PartLicense(CleanEnum):
    """TODO."""

    APACHE = License(
        uuid=UUID("bc058bb8-abd9-419a-860e-43b0889cad89"),
        spdxID="apache-2.0",
        title="Apache License 2.0",
        description=(
            "A permissive license whose main conditions require preservation "
            "of copyright and license notices. Contributors provide an "
            "express grant of patent rights. Licensed works, modifications, "
            "and larger works may be distributed under different terms and "
            "without source code."
        ),
        icon=None,
        url=TypeAdapter(HttpUrl).validate_python(
            "http://www.apache.org/licenses/LICENSE-2.0",
        ),
        osiApproved=True,
    )
    CC_BY = License(
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
    CC_BY_SA = License(
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
    CC0 = License(
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
    GPL = License(
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
    MIT = License(
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
