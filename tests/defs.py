from dataclasses import dataclass

from safestruct import struct, ByteOrder
from safestruct import IntField, BooleanField, SubStructField
from safestruct.descriptors import ArrayField, TextField, BytesField, FloatField


@struct(order=ByteOrder.LITTLE)
@dataclass
class Packet:
    flag: bool = BooleanField()
    sequence: int = IntField("I")


@struct(order=ByteOrder.NETWORK)
@dataclass
class Header:
    version: int = IntField("B")
    length: int = IntField("H")
    status: int = IntField("b", check=lambda x: x >= -1)


@struct(order=ByteOrder.BIG)
@dataclass
class SensorData:
    timestamp: int = IntField("Q")
    readings: list[int] = ArrayField(IntField("I"), count=4)
    checksum: int = IntField("H", check=lambda x: 0xEF00 <= x <= 0xFFFF)


@struct(order=ByteOrder.LITTLE)
@dataclass
class Message:
    header: Header = SubStructField(Header)
    payload_id: int = IntField("L")
    user_id: int = IntField("I")
    username: str = TextField(length=16)
    is_admin: bool = BooleanField()


@struct(order=ByteOrder.LITTLE)
@dataclass
class ProtocolMessage:
    magic: int = IntField("H")
    id: bytes = BytesField(length=4)
    reserved: bytes = BytesField(length=1, check=lambda x: x == b"\x00")


@struct(order=ByteOrder.NETWORK)
@dataclass
class UserRecord:
    user_id: int = IntField("I")
    username: str = TextField(length=16)
    is_admin: bool = BooleanField()


@struct(order=ByteOrder.LITTLE)
@dataclass
class SubStructMessage:
    header: Header = SubStructField(Header)
    payload_id: int = IntField("L")


@struct(order=ByteOrder.LITTLE)
@dataclass
class TelemetryPacket:
    timestamp: int = IntField("Q")
    temperature: float = FloatField("f")
    pressure: float = FloatField("d")
    is_valid: bool = BooleanField("?")
