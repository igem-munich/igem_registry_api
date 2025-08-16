"""Registry API client.

This module defines the `Client` class, the primary programmatic interface to
the iGEM Registry API. It manages connection state, authentication, and
consent-based operations.

Includes:
    Client: The main client class for interacting with the API.
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING

import requests
from pydantic import UUID4, HttpUrl, TypeAdapter

from .calls import _call
from .errors import (
    ClientConnectionError,
)
from .types import ClientMode, HealthCheck, UserData
from .utils import authenticated, connected

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from pydantic import NonNegativeInt

    from .types import RateLimit

logger = logging.getLogger(__name__)


__all__ = [
    "Client",
]


class Client:
    """Registry API client.

    The `Client` class provides the main programmatic interface to the iGEM
    Registry API. It encapsulates connection management, authentication,
    and user consent handling.

    This class is **not** thread-safe and should not be shared across threads
    without external synchronization.
    """

    def __init__(  # noqa: PLR0913
        self,
        base: str | None = "https://api.registry.igem.org/v1",
        *,
        verify: bool | str = True,
        timeout: None | float | tuple[float, None] | tuple[float, float] = (
            5.0,
            30.0,
        ),
        stream: bool = False,
        proxies: MutableMapping[str, str] | None = None,
        certificate: str | tuple[str, str] | None = None,
        redirects: bool = True,
        retries: NonNegativeInt = 3,
    ) -> None:
        """Create a new Registry API client instance.

        The client represents the primary programmatic interface to the iGEM
        Registry. By default, the client starts in offline mode if `base` is
        not provided. With a valid base URL, `connect()` may be used to verify
        the remote instance and enter anonymous mode. For authenticated
        operations, `sign_in()` transitions the client into authenticated mode.
        Consent-based actions such as part authoring or publishing of parts can
        be enabled via `opt_in()`.

        This class is **not** thread-safe. Do not share a single instance
        across threads without external synchronization.

        Args:
            base (str | None): Base URL of the Registry API. If provided, must
                be a valid HTTP URL. If `None`, the client is unable to connect
                to the registry instance (offline mode).
            verify (bool | str): TLS verification setting passed to `requests`.
                Can be set to `False` (disables verification), `True` (enables
                verification), or a path to a CA bundle.
            timeout (None | float | tuple[float, None] | tuple[float, float]):
                Default timeout passed to `requests`. Either a `None` value to
                disable timeouts, a single float specifying both the connect
                and read timeouts, `(connect, None)` to disable read timeout,
                or `(connect, read)` enabling separate timeout values.
            stream (bool): Whether responses should be streamed by default.
            proxies (MutableMapping[str, str] | None): Proxy mapping passed to
                `requests`.
            certificate (str | tuple[str, str] | None): Path to the client
                certificate or a tuple of paths to the certificate and the
                corresponding key files.
            redirects (bool): Whether redirects are allowed by default.
            retries (NonNegativeInt): Retry budget for failed requests. Applies
                to both server-side errors (5xx responses) and API rate-limit
                backoffs. Once exhausted, the request will raise an error.

        Raises:
            pydantic.ValidationError: If `base` string is not a valid HTTP URL.

        Examples:
            ```
            client = Client()
            client.connect()
            client.sign_in("username", "password")
            client.opt_in()
            client.opt_out()
            client.sign_out()
            client.disconnect()
            ```

        """
        logger.info("Initializing client with base URL: %s", base)
        logger.debug(
            "Client configuration: %s",
            {
                "verify": verify,
                "timeout": timeout,
                "stream": stream,
                "proxies": proxies,
                "certificate": certificate,
                "redirects": redirects,
                "retries": retries,
            },
        )
        self.base: HttpUrl | None = (
            TypeAdapter(HttpUrl).validate_python(base.rstrip("/"))
            if base is not None
            else None
        )
        self.mode: ClientMode = ClientMode.NONE
        self.session: requests.Session = requests.Session()

        self.verify = verify
        self.timeout = timeout
        self.stream = stream
        self.proxies = proxies
        self.certificate = certificate
        self.redirects = redirects
        self.retries = retries

        self.ratelimit: RateLimit | None = None
        self.cooldown: NonNegativeInt = 0

        self.username: str | None = None
        self.uuid: UUID4 | None = None
        self.consent: bool | None = None

    @property
    def is_none(self) -> bool:
        """Check if the client is in local mode."""
        return self.mode is ClientMode.NONE

    @property
    def is_anon(self) -> bool:
        """Check if the client is in anonymous mode."""
        return self.mode is ClientMode.ANON

    @property
    def is_auth(self) -> bool:
        """Check if the client is in authenticated mode."""
        return self.mode is ClientMode.AUTH

    @property
    def is_opted_in(self) -> bool:
        """Check if the client is opted in."""
        return self.consent is True

    def connect(self) -> None:
        """Connect the client to the API.

        Raises:
            ClientConnectionError: If the client is already connected, the
            API base URL for connection is not set, or health check of the
            registry API instance fails.

        """
        logger.info("Connecting client to API at base URL: %s", self.base)
        if not self.is_none:
            msg = "Client is already connected."
            logger.error(msg)
            raise ClientConnectionError(msg)
        if self.base is None:
            msg = "API base URL is not set."
            logger.error(msg)
            raise ClientConnectionError(msg)

        health: HealthCheck = inspect.unwrap(Client.health)(self)
        if health.status != "ok":
            msg = f"Health check failed: {health.status}."
            logger.error(msg)
            raise ClientConnectionError(msg)

        self.mode = ClientMode.ANON

    @connected
    def disconnect(self) -> None:
        """Disconnect the client from the API.

        Raises:
            NotConnectedError: If the client is not connected.

        """
        logger.info("Disconnecting client from API.")
        self.session.close()
        self.mode = ClientMode.NONE
        self.username = None
        self.uuid = None
        self.consent = None

    @connected
    def health(self) -> HealthCheck:
        """Check the health of the registry instance.

        Returns:
            out (HealthCheck): The health data of the registry instance.

        Raises:
            NotConnectedError: If the client is not connected.

        """
        return _call(
            self,
            requests.Request(
                method="GET",
                url=f"{self.base}/health",
            ),
            HealthCheck,
        )

    @connected
    def sign_in(
        self,
        username: str,
        password: str,
        instance: str = "https://api.igem.org/v1",
    ) -> None:
        """Authenticate the user.

        Attributes:
            username (str): The username of the user.
            password (str): The password of the user.
            instance (str): The instance URL granting authentication token.

        Raises:
            NotConnectedError: If the client is not connected.

        """
        logger.info("Signing in user %s", username)
        _call(
            self,
            requests.Request(
                method="POST",
                url=f"{instance}/auth/sign-in",
                headers={"Content-Type": "application/json"},
                json={
                    "identifier": username,
                    "password": password,
                },
            ),
        )
        _call(
            self,
            requests.Request(
                method="GET",
                url=f"{self.base}/auth/oauth/default/login",
            ),
        )

        user: UserData = inspect.unwrap(Client.me)(self)

        self.mode = ClientMode.AUTH
        self.username = username
        self.uuid = user.uuid
        self.consent = user.consent

    @authenticated
    def sign_out(self) -> None:
        """Sign out the authenticated user.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        logger.info("Signing out user %s", self.username)
        _call(
            self,
            requests.Request(
                method="POST",
                url=f"{self.base}/auth/sign-out",
            ),
        )

        self.session.cookies.clear()
        self.mode = ClientMode.ANON
        self.username = None
        self.uuid = None
        self.consent = None

    @authenticated
    def me(self) -> UserData:
        """Get information about the authenticated user.

        Returns:
            out (UserData): The authenticated user data.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        return _call(
            self,
            requests.Request(
                method="GET",
                url=f"{self.base}/auth/me",
            ),
            UserData,
        )

    @authenticated
    def opt_in(self) -> None:
        """Opt-in the authenticated user.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        logger.info("Opting in user %s", self.username)
        if self.consent:
            logger.error("User already opted in.")
            return
        _call(
            self,
            requests.Request(
                method="POST",
                url=f"{self.base}/accounts/opt-in",
            ),
        )
        self.consent = True

    @authenticated
    def opt_out(self) -> None:
        """Opt-out the authenticated user.

        Raises:
            NotAuthenticatedError: If the client is not authenticated.

        """
        logger.info("Opting out user %s", self.username)
        if not self.consent:
            logger.error("User already opted out.")
            return
        _call(
            self,
            requests.Request(
                method="POST",
                url=f"{self.base}/accounts/opt-out",
            ),
        )
        self.consent = False
