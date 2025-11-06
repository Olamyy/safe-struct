import struct as stdlib_struct
from dataclasses import dataclass, fields
from typing import Type, Tuple, Any, List

from safestruct.enums import ByteOrder
from safestruct.descriptors import FieldDescriptor, SubStructField, ArrayField
from safestruct.exceptions import (
    ValidationError,
    PackingError,
    UnpackingError,
    FormatError,
)


def _compile_format_string(cls: Type, order: ByteOrder) -> Tuple[str, dict]:
    """Compiles the final struct format string from dataclass fields."""

    prefix = order.to_struct_char()
    format_parts = [prefix]
    field_metadata = {}

    for field in fields(cls):
        descriptor = field.default

        if not isinstance(descriptor, FieldDescriptor):
            raise TypeError(
                f"Field '{field.name}' must use a SafeStruct FieldDescriptor (e.g., IntField)."
            )

        struct_char = descriptor.get_struct_char()
        format_parts.append(struct_char)

        if isinstance(descriptor, SubStructField):
            num_primitives = len(struct_char)
        elif isinstance(descriptor, ArrayField):
            num_primitives = descriptor.get_primitive_count()
        else:
            num_primitives = 1

        field_metadata[field.name] = {
            "char": struct_char,
            "validator": descriptor.get_validator(),
            "descriptor": descriptor,
            "num_primitives": num_primitives,
        }

    return "".join(format_parts), field_metadata


def _flatten_values(instance: Any, cls: Type) -> List[Any]:
    values = []

    for field_name, field_info in cls._safestruct_field_map.items():
        value = getattr(instance, field_name)
        descriptor = field_info["descriptor"]

        if not field_info["validator"](value):
            raise ValidationError(
                f"Validation failed for field '{field_name}' in {cls.__name__}. Value: {value}"
            )

        if isinstance(descriptor, SubStructField):
            packed_sub_bytes = value.pack()

            sub_values = stdlib_struct.unpack(
                descriptor._struct_class._safestruct_format, packed_sub_bytes
            )
            values.extend(sub_values)

        elif hasattr(descriptor, "pack_value"):
            packed_sub_value = descriptor.pack_value(value)

            if isinstance(descriptor, ArrayField):
                values.extend(packed_sub_value)
            else:
                values.append(packed_sub_value)

        else:
            values.append(value)

    return values


def _generate_pack_method(cls: Type):
    """Dynamically creates the .pack() instance method."""

    def pack(self) -> bytes:
        format_string = cls._safestruct_format

        values = _flatten_values(self, cls)

        try:
            return stdlib_struct.pack(format_string, *values)
        except stdlib_struct.error as e:
            raise PackingError(
                f"Packing struct failed for {cls.__name__} (Format: {format_string}): {e}"
            )

    return pack


def _generate_pack_into_method(cls: Type):
    """Dynamically creates the .pack_into(buffer, offset) instance method."""

    def pack_into(self, buffer: bytearray, offset: int = 0):
        format_string = cls._safestruct_format

        values = _flatten_values(self, cls)

        try:
            stdlib_struct.pack_into(format_string, buffer, offset, *values)
        except stdlib_struct.error as e:
            raise PackingError(
                f"Pack into buffer failed for {cls.__name__} (Format: {format_string}): {e}"
            )

    return pack_into


def _generate_unpack_method(cls: Type):
    """Dynamically creates the .unpack() class method."""

    @classmethod
    def unpack(cls, buffer: bytes):
        format_string = cls._safestruct_format

        expected_size = cls._safestruct_size
        if len(buffer) < expected_size:
            raise UnpackingError(
                f"Unpack buffer too small for {cls.__name__}. Expected {expected_size} bytes, got {len(buffer)}."
            )

        try:
            unpacked_values = stdlib_struct.unpack(format_string, buffer)
        except stdlib_struct.error as e:
            raise UnpackingError(
                f"Unpacking struct failed for {cls.__name__} (Format: {format_string}): {e}"
            )

        instance_args = []
        value_cursor = 0

        for field_name, field_info in cls._safestruct_field_map.items():
            descriptor = field_info["descriptor"]
            num_primitives = field_info["num_primitives"]

            primitive_slice = unpacked_values[
                value_cursor : value_cursor + num_primitives
            ]
            value_cursor += num_primitives

            if isinstance(descriptor, SubStructField):
                nested_instance = descriptor._struct_class(*primitive_slice)
                instance_args.append(nested_instance)

            elif isinstance(descriptor, ArrayField):
                instance_args.append(descriptor.unpack_value(primitive_slice))

            elif hasattr(descriptor, "unpack_value"):
                if not primitive_slice:
                    raise UnpackingError(
                        f"Corrupted data for field '{field_name}' during unpack."
                    )

                raw_bytes = primitive_slice[0]
                instance_args.append(descriptor.unpack_value(raw_bytes))

            else:
                if not primitive_slice:
                    raise UnpackingError(
                        f"Corrupted data for field '{field_name}' during unpack."
                    )

                instance_args.append(primitive_slice[0])

        return cls(*instance_args)

    return unpack


def _generate_unpack_from_method(cls: Type):
    """Dynamically creates the .unpack_from(buffer, offset) class method."""

    @classmethod
    def unpack_from(cls, buffer: bytes, offset: int = 0):
        format_string = cls._safestruct_format

        expected_size = cls._safestruct_size

        if len(buffer) < offset + expected_size:
            raise UnpackingError(
                f"Unpack buffer too small for {cls.__name__}. Expected {expected_size} bytes starting "
                f"at offset {offset}, but buffer ends at index {len(buffer)}."
            )

        try:
            unpacked_values = stdlib_struct.unpack_from(format_string, buffer, offset)
        except stdlib_struct.error as e:
            raise UnpackingError(
                f"Unpacking from buffer failed for {cls.__name__} (Format: {format_string}): {e}"
            )

        instance_args = []
        value_cursor = 0

        for field_name, field_info in cls._safestruct_field_map.items():
            descriptor = field_info["descriptor"]
            num_primitives = field_info["num_primitives"]

            primitive_slice = unpacked_values[
                value_cursor : value_cursor + num_primitives
            ]
            value_cursor += num_primitives

            if not primitive_slice and num_primitives > 0:
                raise UnpackingError(
                    f"Corrupted data or unexpected end of buffer for field '{field_name}'."
                )

            if isinstance(descriptor, SubStructField):
                nested_instance = descriptor._struct_class(*primitive_slice)
                instance_args.append(nested_instance)

            elif isinstance(descriptor, ArrayField):
                instance_args.append(descriptor.unpack_value(primitive_slice))

            elif hasattr(descriptor, "unpack_value"):
                raw_bytes = primitive_slice[0]
                instance_args.append(descriptor.unpack_value(raw_bytes))

            else:
                instance_args.append(primitive_slice[0])

        return cls(*instance_args)

    return unpack_from


def struct(order: ByteOrder):
    """
    Decorator that transforms a dataclass into a SafeStruct definition.
    Requires explicit byte ordering (LITTLE, BIG, or NETWORK).
    """

    if order in (ByteOrder.NATIVE, ByteOrder.STANDARD):
        raise FormatError(
            "SafeStruct requires explicit LITTLE ('<'), BIG ('>'), or NETWORK ('!') byte order "
            "to guarantee cross-platform compatibility."
        )

    def wrap(cls):
        if not hasattr(cls, "__dataclass_fields__"):
            cls = dataclass(cls)

        final_order = order

        format_string, field_map = _compile_format_string(cls, final_order)

        cls._safestruct_format = format_string
        cls._safestruct_field_map = field_map
        cls._safestruct_size = stdlib_struct.calcsize(format_string)

        setattr(cls, "pack", _generate_pack_method(cls))
        setattr(cls, "unpack", _generate_unpack_method(cls))
        setattr(cls, "format_string", property(lambda self: cls._safestruct_format))
        setattr(cls, "size", property(lambda self: cls._safestruct_size))
        setattr(cls, "field_info", property(lambda self: cls._safestruct_field_map))
        setattr(cls, "pack_into", _generate_pack_into_method(cls))
        setattr(cls, "unpack_from", _generate_unpack_from_method(cls))

        return cls

    return wrap
