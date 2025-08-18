"""Utilities for handling API rate limits.

Includes:
    _ratelimit: A function to extract rate limit information from headers.
    _cooldown: A function to calculate cooldown duration based on rate limits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, NonNegativeInt

from .schemas import FrozenModel

if TYPE_CHECKING:
    from requests.structures import CaseInsensitiveDict

WINDOWS: tuple[str, str, str] = ("short", "medium", "large")
METRICS: tuple[str, str, str] = ("remaining", "reset", "limit")

RATE_LIMIT_HEADERS: tuple[str, ...] = tuple(
    f"x-ratelimit-{metric}-{window}"
    for metric in METRICS
    for window in WINDOWS
)
RETRY_AFTER_HEADERS: tuple[str, ...] = tuple(
    f"retry-after-{window}" for window in WINDOWS
)


__all__ = [
    "cooldown",
    "ratelimit",
]


class RateLimit(FrozenModel):
    """Rate limit information model for API requests."""

    balance: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Balance",
        description=(
            "Remaining requests for short, medium, and large call windows"
        ),
        default=(0, 0, 0),
        alias="remaining",
    )
    reset: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Reset",
        description=(
            "Reset times (seconds) for short, medium, and large call windows"
        ),
        default=(5, 60, 600),
        alias="reset",
    )
    quota: tuple[NonNegativeInt, NonNegativeInt, NonNegativeInt] = Field(
        title="Quota",
        description=(
            "Request limits for short, medium, and large call windows"
        ),
        default=(5, 60, 200),
        alias="limit",
    )


def ratelimit(
    headers: CaseInsensitiveDict,
) -> RateLimit:
    """Extract rate limit information from response headers.

    Args:
        headers (CaseInsensitiveDict): The response headers from which to
            extract rate limit information.

    Returns:
        out (RateLimit): Extracted rate limit information, including total
            request limits, remaining requests, and reset times for the short,
            medium, and large API call windows.

    """
    data: dict[str, tuple[int, int, int]] = {}

    for metric in METRICS:
        values = (
            int(headers.get(f"x-ratelimit-{metric}-short", -1)),
            int(headers.get(f"x-ratelimit-{metric}-medium", -1)),
            int(headers.get(f"x-ratelimit-{metric}-large", -1)),
        )

        if -1 in values:
            continue

        data[metric] = values

    return RateLimit(**data)


def cooldown(ratelimit: RateLimit) -> NonNegativeInt:
    """Calculate the cooldown duration based on the rate limit information.

    Args:
        ratelimit (RateLimit): The rate limit information to use for
            calculating the cooldown.

    Returns:
        out (NonNegativeInt): The calculated cooldown duration (seconds).

    """
    waits = [
        time
        for calls, time in zip(
            ratelimit.balance,
            ratelimit.reset,
            strict=False,
        )
        if calls == 0
    ]
    return max(waits, default=0)
