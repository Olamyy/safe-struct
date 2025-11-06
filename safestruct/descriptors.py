from typing import Callable, Any, Type
from .exceptions import FormatError, PackingError


class FieldDescriptor:
    def __init__(
        self, struct_char: str, *, check: Callable[[Any], bool] = lambda x: True
    ):
        self._struct_char = struct_char
        self._validator = check
        self.default = self

    def get_struct_char(self) -> str:
        return self._struct_char

    def get_validator(self) -> Callable:
        return self._validator


_INTEGER_LIMITS = {
    # Signed
    "b": (-128, 127),  # signed char (1 byte)
    "h": (-32768, 32767),  # signed short (2 bytes)
    "i": (-2147483648, 2147483647),  # signed int (4 bytes)
    "l": (
        -9223372036854775808,
        9223372036854775807,
    ),  # signed long (8 bytes assumed for safety)
    "q": (-9223372036854775808, 9223372036854775807),  # signed long long (8 bytes)
    # Unsigned
    "B": (0, 255),  # unsigned char (1 byte)
    "H": (0, 65535),  # unsigned short (2 bytes)
    "I": (0, 4294967295),  # unsigned int (4 bytes)
    "L": (0, 18446744073709551615),  # unsigned long (8 bytes assumed for safety)
    "Q": (0, 18446744073709551615),  # unsigned long long (8 bytes)
}


class IntField(FieldDescriptor):
    def __init__(
        self, struct_char: str, *, check: Callable[[int], bool] = lambda x: True
    ):
        base_char = struct_char.lstrip("@=<>!")
        if base_char not in _INTEGER_LIMITS:
            raise FormatError(
                f"'{struct_char}' is not a supported integer format char."
            )

        super().__init__(struct_char, check=check)

        self._min_val, self._max_val = _INTEGER_LIMITS[base_char]
        print(
            "Min/Max:",
            self._min_val,
            self._max_val,
            "for char:",
            base_char,
            struct_char,
        )

    def get_validator(self) -> Callable:
        base_validator = super().get_validator()

        def combined_check(value: int) -> bool:
            if not isinstance(value, int):
                return False

            if not (self._min_val <= value <= self._max_val):
                return False

            return base_validator(value)

        return combined_check


class BooleanField(FieldDescriptor):
    def __init__(
        self, struct_char: str = "?", *, check: Callable[[bool], bool] = lambda x: True
    ):
        if struct_char != "?":
            raise FormatError(
                f"BooleanField must use '?' format char, got '{struct_char}'."
            )

        super().__init__(struct_char, check=check)

    def get_validator(self) -> Callable:
        base_validator = super().get_validator()

        def combined_check(value: bool) -> bool:
            if not isinstance(value, bool):
                return False
            return base_validator(value)

        return combined_check


class BytesField(FieldDescriptor):
    """
    A descriptor for fixed-length bytes/string types ('Ns' format).
    """

    def __init__(self, length: int, *, check: Callable[[bytes], bool] = lambda x: True):
        if not isinstance(length, int) or length <= 0:
            raise FormatError("BytesField requires a positive integer 'length'.")

        struct_char = f"{length}s"
        super().__init__(struct_char, check=check)
        self._length = length

    def get_validator(self) -> Callable:
        base_validator = super().get_validator()

        def combined_check(value: bytes) -> bool:
            if not isinstance(value, (bytes, bytearray)):
                return False

            if len(value) != self._length:
                return False

            return base_validator(value)

        return combined_check

    @staticmethod
    def pack_value(value: bytes) -> bytes:
        """For 'Ns' fields, the value is simply passed through (already validated)."""
        return value

    @staticmethod
    def unpack_value(raw_bytes: bytes) -> bytes:
        """For 'Ns' fields, the value is simply passed through as raw bytes."""
        return raw_bytes


class SubStructField(FieldDescriptor):
    """
    A descriptor for nesting one SafeStruct inside another.
    """

    def __init__(self, struct_class: Type):
        if not hasattr(struct_class, "_safestruct_format"):
            raise FormatError(
                f"'{struct_class.__name__}' is not a valid SafeStruct. "
                "Did you forget to apply the @struct decorator?"
            )

        self._struct_class = struct_class

        nested_format_full = struct_class._safestruct_format
        nested_char_only = nested_format_full[1:]

        super().__init__(nested_char_only)

    def get_struct_char(self) -> str:
        return self._struct_char


class TextField(FieldDescriptor):
    """
    A descriptor for fixed-length encoded strings ('Ns' format).
    Handles encoding, null-byte padding, and stripping.
    """

    def __init__(
        self,
        length: int,
        encoding: str = "utf-8",
        *,
        check: Callable[[str], bool] = lambda x: True,
    ):
        if not isinstance(length, int) or length <= 0:
            raise FormatError("TextField requires a positive integer 'length'.")

        struct_char = f"{length}s"
        super().__init__(struct_char, check=check)
        self._length = length
        self._encoding = encoding

    def get_validator(self) -> Callable:
        base_validator = super().get_validator()

        def combined_check(value: str) -> bool:
            if not isinstance(value, str):
                return False

            try:
                if len(value.encode(self._encoding)) > self._length:
                    return False
            except Exception as _:
                return False

            return base_validator(value)

        return combined_check

    def pack_value(self, value: str) -> bytes:
        """Encodes the string and pads it with null bytes to reach fixed length."""
        encoded = value.encode(self._encoding)
        if len(encoded) > self._length:
            raise PackingError(
                f"Encoded string '{value}' exceeds fixed size {self._length} bytes."
            )

        return encoded.ljust(self._length, b"\x00")

    def unpack_value(self, raw_bytes: bytes) -> str:
        """Strips trailing null bytes (0x00) and decodes the result."""
        null_index = raw_bytes.find(b"\x00")
        data_bytes = raw_bytes[:null_index] if null_index != -1 else raw_bytes

        return data_bytes.decode(self._encoding)


class ArrayField(FieldDescriptor):
    """
    A descriptor for fixed-length arrays of primitive types (e.g., '4I').
    """

    def __init__(self, item_descriptor: FieldDescriptor, count: int):
        if not isinstance(count, int) or count <= 0:
            raise FormatError("ArrayField requires a positive integer 'count'.")

        if not isinstance(item_descriptor, (IntField, BooleanField)):
            raise FormatError(
                "ArrayField currently only supports IntField or BooleanField primitives."
            )

        self._count = count
        self._item_descriptor = item_descriptor

        item_char = item_descriptor.get_struct_char()
        if len(item_char) > 1:
            raise FormatError(
                "ArrayField does not support variable-length or complex inner formats."
            )

        struct_char = f"{count}{item_char}"

        super().__init__(struct_char, check=lambda x: True)

    def get_validator(self) -> Callable:
        def combined_check(value: list) -> bool:
            if not isinstance(value, list) or len(value) != self._count:
                return False

            item_validator = self._item_descriptor.get_validator()
            return all(item_validator(item) for item in value)

        return combined_check

    def pack_value(self, value: list) -> list:
        """Flattens the list for struct.pack."""
        return value

    def unpack_value(self, values: tuple) -> list:
        """Reassembles the tuple slice back into a list."""
        return list(values)

    def get_primitive_count(self):
        return self._count
