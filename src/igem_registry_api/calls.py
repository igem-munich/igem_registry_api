"""Core request execution and error handling utilities.

This submodule provides the central request execution logic for the client,
including unified error handling, retry and backoff strategies, and optional
response validation against Pydantic models. It forms the foundation for all
API interactions within the wrapper.

Includes:
    _call: A function for executing a single HTTP request.
    _call_paginated: A function for executing paginated HTTP requests.
"""

from __future__ import annotations

import logging
from http import HTTPStatus
from time import sleep
from typing import TYPE_CHECKING, overload

from pydantic import BaseModel, Field, NonNegativeInt, ValidationError

from .__meta__ import __repository__, __title__, __version__
from .errors import (
    ClientError,
    EmptyBodyError,
    HTTPError,
    RateLimitError,
    ResponseValidationError,
    RetryExhaustedError,
    ServerError,
    TransportError,
)
from .rates import (
    RATE_LIMIT_HEADERS,
    RETRY_AFTER_HEADERS,
    _cooldown,
    _ratelimit,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from requests import Request

    from .client import Client


logger = logging.getLogger(__name__)


__all__ = [
    "_call",
    "_call_paginated",
]


class PaginatedResponse[
    ResponseObject: BaseModel,
    MetadataObject: BaseModel | None,
](
    BaseModel,
):
    """Generic model for API responses that return paginated data.

    This model wraps a list of response objects together with the current page
    number, the total number of available objects, and optional metadata
    provided by the API.
    """

    data: list[ResponseObject] = Field(
        title="Data",
        description="A list of data objects returned in the response.",
        min_length=0,
        max_length=100,
    )
    page: int = Field(
        title="Page",
        description="The current page number.",
        ge=1,
    )
    total: int = Field(
        title="Total",
        description="The total number of objects available.",
        ge=0,
    )
    metadata: MetadataObject | None = Field(
        title="Metadata",
        description="Additional metadata about the response.",
        default=None,
    )


@overload
def _call(
    client: Client,
    request: Request,
    data: None = None,
) -> None: ...


@overload
def _call[ResponseObject: BaseModel](
    client: Client,
    request: Request,
    data: type[ResponseObject],
) -> ResponseObject: ...


def _call(  # noqa: C901, PLR0912, PLR0915
    client,
    request,
    data=None,
):
    """Perform a single API call.

    This function prepares and dispatches a `requests.Request` using the
    provided `Client` session. It implements retry logic for transient server
    and rate-limiting errors, updates client-side rate-limit state, and
    optionally validates the response body against a Pydantic model.

    Function behavior:
    - Ensures that a default `User-Agent` header is present, based on the
        library's metadata, unless explicitly set by the caller.
    - Prepares and sends the request using the client's configured
        `requests.Session`.
    - Applies a pre-request cooldown delay (`client.cooldown`) before
        sending each attempt, based on the current rate limit.
    - Retries the request (`client.retries` times) in the following cases:
        - 5xx server errors: exponential backoff is applied, doubling
            `client.cooldown` up to a maximum of 60 seconds.
        - 429 Too Many Requests: `client.cooldown` is set from
            `Retry-After` headers when available, or defaults to a fallback
            value.
    - Updates the client's rate-limit state (`client.ratelimit`) and
        recalculates `client.cooldown` for the following call if the response
        contains headers defined in `RATE_LIMIT_HEADERS`.
    - Treats any non-successful HTTP status (outside the 2xx range) as an
        error and raises an appropriate exception.
    - If `data` is provided, attempts to parse and validate the response
        body into an instance of the specified Pydantic model.
    - If `data` is omitted or `client.stream` is enabled, the function
        does not parse the body and instead returns `None`.

    Args:
        client (Client): The `Client` instance that holds the HTTP session,
            retry configuration, and rate-limit state.
        request (Request): A `requests.Request` object defining the HTTP
            request to send.
        data (type[ResponseObject] | None): Optional Pydantic model of the
            response body. When provided, function returns a validated
            instance of this model. If omitted, the function returns `None`.

    Returns:
        out (type[ResponseObject] | None): None if no schema is provided or
        streaming is enabled. Otherwise, an instance of the specified Pydantic
        model containing the validated response data.

    Raises:
        TransportError: If a network or transport-level failure occurs before
            an HTTP response is received.
        RetryExhaustedError: If the request fails after exhausting all retry
            attempts.
        RateLimitError: If the server responds with HTTP 429 Too Many Requests.
        ClientError: For other 4xx client-side HTTP errors.
        ServerError: For 5xx server-side HTTP errors not recovered through
            retries.
        HTTPError: For any other unexpected non-success HTTP status.
        EmptyBodyError: If a response is received without content when a body
            is required for validation.
        ResponseValidationError: If the response body cannot be parsed or fails
            validation against the specified Pydantic model.

    """
    request.headers.setdefault(
        "User-Agent",
        f"{__title__}/{__version__} (+{__repository__})",
    )

    for attempt in range(client.retries):
        if attempt > 0:
            logger.warning(
                "Retrying '%s' request to '%s', attempt %s.",
                request.method,
                request.url,
                attempt,
            )

        prepared = client.session.prepare_request(request)
        logger.debug(
            "Prepared '%s' request to '%s' with headers: '%s', body: '%s'.",
            prepared.method,
            prepared.url,
            prepared.headers,
            prepared.body,
        )

        if client.cooldown:
            logger.debug(
                "Cooldown before sending '%s' request to '%s': %s seconds.",
                prepared.method,
                prepared.url,
                client.cooldown,
            )
        sleep(client.cooldown or 0)

        try:
            response = client.session.send(
                request=prepared,
                verify=client.verify,
                timeout=client.timeout,
                stream=client.stream,
                proxies=client.proxies,
                cert=client.certificate,
                allow_redirects=client.redirects,
            )
        except Exception as e:
            msg = (
                f"Transport error occurred during '{prepared.method}' "
                f"request to '{prepared.url}': {e}"
            )
            logger.error(msg)  # noqa: TRY400
            raise TransportError(msg) from e

        status = HTTPStatus(response.status_code)

        if status.is_server_error:
            client.cooldown = min((client.cooldown or 1) * 2, 60)
            logger.warning(
                "Server error for '%s' request to '%s': %s, %s. "
                "Retrying in %s seconds.",
                prepared.method,
                prepared.url,
                response.status_code,
                response.reason,
                client.cooldown,
            )
            continue

        if status == HTTPStatus.TOO_MANY_REQUESTS:
            client.cooldown = max(
                int(response.headers.get(header, 1))
                for header in RETRY_AFTER_HEADERS
            )
            logger.warning(
                "Rate limit exceeded for '%s' request to '%s': %s, %s. "
                "Retrying in %s seconds.",
                prepared.method,
                prepared.url,
                response.status_code,
                response.reason,
                client.cooldown,
            )
            continue

        break
    else:
        msg = (
            f"Retries exhausted for '{request.method}' request "
            f"to '{request.url}': {client.retries} retries."
        )
        logger.error(msg)
        raise RetryExhaustedError(msg)

    logger.debug(
        "Response for '%s' request to '%s': %s, %s. Response headers: %s",
        prepared.method,
        prepared.url,
        response.status_code,
        response.reason,
        response.headers,
    )

    if all(header in response.headers for header in RATE_LIMIT_HEADERS):
        client.ratelimit = _ratelimit(response.headers)
        client.cooldown = _cooldown(client.ratelimit)

    if not status.is_success:
        msg = (
            f"'{request.method}' request to '{request.url}' "
            f"failed with: {response.status_code}, {response.reason}."
        )
        logger.error(msg)
        match status:
            case HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError(
                    response.status_code,
                    response.reason,
                    response.request.method,
                    response.request.url,
                )
            case status.is_client_error:
                raise ClientError(
                    response.status_code,
                    response.reason,
                    response.request.method,
                    response.request.url,
                )
            case status.is_server_error:
                raise ServerError(
                    response.status_code,
                    response.reason,
                    response.request.method,
                    response.request.url,
                )
            case _:
                raise HTTPError(
                    response.status_code,
                    response.reason,
                    response.request.method,
                    response.request.url,
                )

    if data is None or client.stream:
        return None

    if not response.content:
        msg = (
            f"Empty response content for '{request.method}' request to "
            f"'{request.url}': {response.status_code}, {response.reason}."
        )
        logger.error(msg)
        raise EmptyBodyError(msg)

    try:
        logger.debug(
            "Response content for '%s' request to '%s': %s",
            request.method,
            request.url,
            response.content[:500],
        )
        return data.model_validate_json(response.content)
    except ValidationError as e:
        msg = (
            f"Failed to parse response content for '{request.method}' "
            f"request to '{request.url}': {response.content[:500]}. "
            f"Error: {e}."
        )
        logger.error(msg)  # noqa: TRY400
        raise ResponseValidationError(msg) from e


def _call_paginated[  # noqa: PLR0913
    ResponseObject: BaseModel,
    MetadataObject: BaseModel | None,
](
    client: Client,
    request: Request,
    data: type[ResponseObject],
    meta: type[MetadataObject] | None = None,
    *,
    limit: NonNegativeInt | None = None,
    progress: Callable | None = None,
) -> tuple[list[ResponseObject], MetadataObject | None]:
    """Perform a paginated API call.

    This function repeatedly invokes `_call` to fetch multiple pages of results
    from an endpoint that uses page-based data retrieval. It aggregates all
    items across pages into a single list and optionally returns the response
    metadata associated with the paginated data.

    Function behavior:
    - Initializes the request with default pagination parameters:
        first page `"page" = 1` and the maximum page size `"pageSize" = 100`.
    - Calls `_call` iteratively with `PaginatedResponse[data, meta]` until
        an empty page is returned, indicating the end of available data.
    - Accumulates all `data` objects across pages into a result list.
    - Returns response `metadata` from the last page if a metadata schema
        is provided.

    Args:
        client (Client): The `Client` instance that holds the HTTP session,
            retry configuration, and rate-limit state.
        request (Request): A `requests.Request` object defining the HTTP
            request to send.
        data (type[ResponseObject] | None): Pydantic model of the
            response body used for its validation.
        meta (type[ResponseObject] | None): Optional Pydantic model of the
            response metadata. When provided, function returns a validated
            instance of this model. If omitted, the function returns `None`.
        limit (NonNegativeInt | None): Optional maximum number of items to
            retrieve. If provided, pagination stops when this limit is reached.
        progress (Callable | None): Optional callback function to report
            progress updates during pagination. It receives two arguments:
            - `current`: The current number of items retrieved.
            - `total`: The total number of items to retrieve.

    Returns:
        out (tuple[list[ResponseObject], MetadataObject | None]): A tuple
            containing a list of items retrieved across all pages and
            optionally the associated response metadata.

    Raises:
        TransportError: If a network or transport-level failure occurs before
            an HTTP response is received.
        RetryExhaustedError: If a request fails after exhausting all retry
            attempts.
        RateLimitError: If the server responds with HTTP 429 Too Many Requests.
        ClientError: For other 4xx client-side HTTP errors.
        ServerError: For 5xx server-side HTTP errors not recovered through
            retries.
        HTTPError: For any other unexpected non-success HTTP status.
        EmptyBodyError: If a response is received without content when a body
            is required for validation.
        ResponseValidationError: If the response body cannot be parsed or fails
            validation against the specified Pydantic model.

    """
    results: list[ResponseObject] = []

    if request.params is None:
        request.params = {}
    request.params["page"] = 1
    request.params["pageSize"] = 100

    logger.debug(
        "Starting pagination for '%s' request to '%s'.",
        request.method,
        request.url,
    )

    while True:
        response = _call(
            client,
            request,
            PaginatedResponse[data, meta],
        )

        logger.debug(
            "Received page %s for '%s' request to '%s' with %s items.",
            request.params["page"],
            request.method,
            request.url,
            len(response.data),
        )

        if len(response.data) == 0:
            logger.debug(
                "No more items for '%s' request to '%s' at page %s, "
                "stopping pagination.",
                request.method,
                request.url,
                request.params["page"],
            )
            break

        results.extend(response.data)
        if progress:
            progress(
                current=len(results),
                total=min(limit or int("inf"), response.total),
            )

        if limit is not None and len(results) >= limit:
            logger.debug(
                "Reached limit of %s items for '%s' request to '%s', "
                "stopping pagination.",
                limit,
                request.method,
                request.url,
            )
            break

        request.params["page"] += 1
        logger.debug(
            "Cumulative items for '%s' request to '%s': %s. "
            "Moving to next page: %s.",
            request.method,
            request.url,
            len(results),
            request.params["page"],
        )

    logger.debug(
        "Final cumulative items: %s.",
        len(results),
    )

    if meta is not None:
        logger.debug(
            "Metadata of the paginated response for '%s' request to '%s': %s",
            request.method,
            request.url,
            response.metadata,
        )

    return results[:limit] if limit is not None else results, response.metadata
