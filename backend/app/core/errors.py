class CortexError(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(CortexError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, status_code=401)


class PermissionDeniedError(CortexError):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class NotFoundError(CortexError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class IngestionError(CortexError):
    def __init__(self, message: str = "Document ingestion failed"):
        super().__init__(message, status_code=422)


class SSRFSecurityError(CortexError):
    def __init__(self, message: str = "Access to private or non-routable IP addresses is forbidden"):
        super().__init__(message, status_code=400)
