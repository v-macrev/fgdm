from __future__ import annotations


class FGDMError(Exception):
    """Base exception for FGDM."""


class ValidationError(FGDMError):
    """Raised when input data fails validation."""


class ConfigurationError(FGDMError):
    """Raised when configuration is invalid or inconsistent."""