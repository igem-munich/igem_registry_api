"""Custom exceptions for the API client.

Includes:
    ApiError: Base for all wrapper errors.
    TransportError: Network/transport-level failure before an HTTP response is
        available.
    RetryExhaustedError: Exhausted maximum number of retry attempts
        (429/5xx/backoff).
    HTTPError: HTTP response returned non-success status.
    ClientError: 4xx client errors.
    ServerError: 5xx server errors.
    RateLimitError: 429 Too Many Requests.
    EmptyBodyError: Expected a body but response content was empty.
    ResponseValidationError: Pydantic validation failed for the response body.
    ClientConnectionError: Error during the connection process to a registry
        API instance.
    NotConnectedError: Exception raised when the client is not connected.
    NotAuthenticatedError: Exception raised when a user is not authenticated.
    NotOptedInError: Exception raised when a user has not opted in to be a
        contributor.

"""

from __future__ import annotations


class ApiError(Exception):
    """Base for all wrapper errors."""


class TransportError(ApiError):
    """Network/transport-level failure before an HTTP response is available."""


class RetryExhaustedError(ApiError):
    """Exhausted maximum number of retry attempts (429/5xx/backoff)."""


class HTTPError(ApiError):
    """HTTP response returned non-success status."""

    def __init__(
        self,
        status: int,
        reason: str,
        method: str | None,
        url: str | None,
        message: str | None = None,
    ) -> None:
        """Initialize an instance of the error class.

        Args:
            status (int): The HTTP status code of the response.
            reason (str): The reason phrase associated with the status code.
            method (str | None): The HTTP method used for the request
                (e.g., 'GET', 'POST', 'PATCH', 'DELETE').
            url (str | None): Full URL of the request (including base,
                endpoint, and parameters).
            message (str | None): A custom error message. Defaults to a
                formatted string combining method, url, status, and reason.

        Returns:
            out (None):

        """
        self.status = status
        self.reason = reason
        self.method = method
        self.url = url
        super().__init__(message or f"{method} {url} -> {status} ({reason})")


class ClientError(HTTPError):
    """4xx client errors."""


class ServerError(HTTPError):
    """5xx server errors."""


class RateLimitError(ClientError):
    """429 Too Many Requests."""


class EmptyBodyError(ApiError):
    """Expected a body but response content was empty."""


class ResponseValidationError(ApiError):
    """Pydantic validation failed for the response body."""


class ClientConnectionError(ApiError):
    """Error during the connection process to a registry API instance."""


class NotConnectedError(ApiError):
    """Exception raised when the client is not connected."""


class NotAuthenticatedError(ApiError):
    """Exception raised when a user is not authenticated."""


class NotOptedInError(ApiError):
    """Exception raised when a user has not opted in to be a contributor."""
