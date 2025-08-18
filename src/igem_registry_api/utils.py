"""General utility functions for the API client.

This module provides various utility functions and decorators for the API
client, including connection and authentication checks.

Includes:
    connected: Decorator to require a connected client.
    authenticated: Decorator to require an authenticated client.
    consented: Decorator to require a opted in client.
"""

from __future__ import annotations

import logging
from enum import Enum
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

import pydantic_core
from pydantic import BaseModel

from .errors import NotAuthenticatedError, NotConnectedError, NotOptedInError

if TYPE_CHECKING:
    from collections.abc import Callable

    from .client import Client


logger = logging.getLogger(__name__)


def connected[**Params, Return](
    func: Callable[Params, Return],
) -> Callable[Params, Return]:
    """Require that the given client is connected.

    The decorated function must take a `client` argument as its first
    positional parameter or as a keyword argument. The decorator inspects
    that client object and raises a :class:`NotConnectedError` if it is in
    a disconnected state (`client.is_none` is True).

    Args:
        func (Callable[Params, Return]): The function to decorate. It must
            accept a `client` parameter as its first argument or via keyword.

    Returns:
        out (Callable[Params, Return]): The wrapped function, which will raise
            :class:`NotConnectedError` if the client is not connected.

    """

    @wraps(func)
    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
        target = kwargs.get("client", args[0])
        if hasattr(target, "client"):
            client = cast("Client", getattr(target, "client"))  # noqa: B009
        else:
            client = cast("Client", target)
        logger.debug(
            "Verifying client connection for function '%s'. "
            "Identified function's client parameter of type '%s'.",
            func.__name__,
            type(client),
        )
        if client.is_none:
            msg = f"Connection required for {func.__name__}()"
            logger.error(msg)
            raise NotConnectedError(msg)
        return func(*args, **kwargs)

    return wrapper


def authenticated[**Params, Return](
    func: Callable[Params, Return],
) -> Callable[Params, Return]:
    """Require that the given client is authenticated.

    The decorated function must take a `client` argument as its first
    positional parameter or as a keyword argument. The decorator inspects
    that client object and raises a :class:`NotAuthenticatedError` if it
    is not authenticated (`client.is_auth` is False).

    Args:
        func (Callable[Params, Return]): The function to decorate. It must
            accept a `client` parameter as its first argument or via keyword.

    Returns:
        out (Callable[Params, Return]): The wrapped function, which will raise
            :class:`NotAuthenticatedError` if the client is not authenticated.

    """

    @wraps(func)
    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
        target = kwargs.get("client", args[0])
        if hasattr(target, "client"):
            client = cast("Client", getattr(target, "client"))  # noqa: B009
        else:
            client = cast("Client", target)
        logger.debug(
            "Verifying client authentication for function '%s'. "
            "Identified function's client parameter of type '%s'.",
            func.__name__,
            type(client),
        )
        if not client.is_auth:
            msg = f"Authentication required for {func.__name__}()"
            logger.error(msg)
            raise NotAuthenticatedError(msg)
        return func(*args, **kwargs)

    return wrapper


def consented[**Params, Return](
    func: Callable[Params, Return],
) -> Callable[Params, Return]:
    """Require that the given client has opted in to be a contributor.

    The decorated function must take a `client` argument as its first
    positional parameter or as a keyword argument. The decorator inspects
    that client object and raises a :class:`NotOptedInError` if it
    is not opted in (`client.is_opted_in` is False).

    Args:
        func (Callable[Params, Return]): The function to decorate. It must
            accept a `client` parameter as its first argument or via keyword.

    Returns:
        out (Callable[Params, Return]): The wrapped function, which will raise
            :class:`NotOptedInError` if the client is not opted in.

    """

    @wraps(func)
    def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
        target = kwargs.get("client", args[0])
        if hasattr(target, "client"):
            client = cast("Client", getattr(target, "client"))  # noqa: B009
        else:
            client = cast("Client", target)
        logger.debug(
            "Verifying whether client has opted in for function '%s'. "
            "Identified function's client parameter of type '%s'.",
            func.__name__,
            type(client),
        )
        if not client.is_opted_in:
            msg = f"Opt-in required for {func.__name__}()"
            logger.error(msg)
            raise NotOptedInError(msg)
        return func(*args, **kwargs)

    return wrapper


class CleanEnum(Enum):
    """Base enum with clean representation."""

    def __repr__(self) -> str:
        """Return a string representation of the enum member."""
        return f"{self.__class__.__name__}.{self.name}"

    def __str__(self) -> str:
        """Return the string value of the enum member."""
        return self.name


def dump(**kwargs: Any) -> Callable:
    """TODO."""

    def base_encoder(obj: object) -> dict:
        """TODO."""
        if isinstance(obj, BaseModel):
            return obj.model_dump(**kwargs)
        return pydantic_core.to_jsonable_python(obj)

    return base_encoder
