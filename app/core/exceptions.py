"""
Signal — Custom Exceptions
App-specific exception classes for structured error handling.
"""

from fastapi import HTTPException, status


class SignalException(HTTPException):
    """Base exception for Signal app."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationError(SignalException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ResourceNotFoundError(SignalException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{resource_id}' not found",
        )


class LLMProviderError(SignalException):
    def __init__(self, provider: str, error: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Provider '{provider}' error: {error}",
        )


class GmailSyncError(SignalException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gmail Sync error: {detail}",
        )
