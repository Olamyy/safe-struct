class InvalidFormatError(ValueError):
    pass


class SafeStructError(Exception):
    """Base exception for all errors raised by the safe-struct library."""

    ...


class FormatError(SafeStructError, ValueError):
    """
    Raised when a field descriptor is initialized with an invalid struct format
    character or an invalid length/argument.
    """

    ...


class ValidationError(SafeStructError, TypeError):
    """
    Raised during packing or unpacking when a value fails a type check or a
    user-defined custom validation function.
    """

    ...


class PackingError(SafeStructError):
    """
    Raised during .pack() when the underlying struct.pack() call fails due
    to a low-level issue (e.g., value out of range for the format code).
    """

    ...


class UnpackingError(SafeStructError):
    """
    Raised during .unpack() when the buffer size is incorrect or the
    underlying struct.unpack() fails (e.g., unexpected EOF).
    """

    ...
