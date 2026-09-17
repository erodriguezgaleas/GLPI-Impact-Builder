"""Custom exceptions for GLPI Impact Builder."""

class GLPIError(Exception):
    """Base exception for the SDK."""

class LoginError(GLPIError):
    """Raised when authentication fails."""

class BrowserError(GLPIError):
    """Raised for browser automation errors."""

class ImpactError(GLPIError):
    """Raised for impact graph errors."""
