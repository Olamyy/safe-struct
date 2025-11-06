from safestruct.core import struct
from safestruct.descriptors import (
    IntField,
    BytesField,
    BooleanField,
    SubStructField,
    ArrayField,
    TextField,
    FloatField,
)
from safestruct.exceptions import (
    FormatError,
    InvalidFormatError,
    PackingError,
    SafeStructError,
    UnpackingError,
    ValidationError,
)
from safestruct.enums import ByteOrder


uint8 = IntField("B")
uint16 = IntField("H")
uint32 = IntField("I")
uint64 = IntField("Q")

int8 = IntField("b")
int16 = IntField("h")
int32 = IntField("i")
int64 = IntField("q")

float32 = FloatField("f")
float64 = FloatField("d")

__all__ = [
    "struct",
    "IntField",
    "BytesField",
    "BooleanField",
    "SubStructField",
    "ArrayField",
    "TextField",
    "FloatField",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "int8",
    "int16",
    "int32",
    "int64",
    "float32",
    "float64",
    "ByteOrder",
    "SafeStructError",
    "FormatError",
    "InvalidFormatError",
    "ValidationError",
    "PackingError",
    "UnpackingError",
]
