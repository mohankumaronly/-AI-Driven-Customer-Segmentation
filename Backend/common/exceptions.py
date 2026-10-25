class AppException(Exception):
    status_code = 400

    def __init__(self, message: str, errors: list[dict] | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors
        if status_code is not None:
            self.status_code = status_code


class ValidationError(AppException):
    status_code = 400

    def __init__(self, message: str = "Request validation failed.", errors: list[dict] | None = None):
        super().__init__(message, errors=errors, status_code=400)


class AuthenticationError(AppException):
    status_code = 401

    def __init__(self, message: str = "Authentication is required."):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    status_code = 403

    def __init__(self, message: str = "Access forbidden."):
        super().__init__(message, status_code=403)


class NotFoundError(AppException):
    status_code = 404

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    status_code = 409

    def __init__(self, message: str = "Resource conflict."):
        super().__init__(message, status_code=409)


class RateLimitExceededError(AppException):
    status_code = 429

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)
