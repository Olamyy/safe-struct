import unittest
import struct as stdlib_struct
from dataclasses import dataclass

from safestruct import struct
from safestruct import ValidationError, UnpackingError
from safestruct import IntField, BooleanField
from safestruct.enums import ByteOrder
from tests.defs import UserRecord, Header, Packet, SensorData


class TestSafeStructCore(unittest.TestCase):
    def test_format_string_compilation(self):
        self.assertEqual(Header._safestruct_format, "!BHb")
        self.assertEqual(Header._safestruct_size, 4)
        self.assertEqual(Packet._safestruct_format, "<?I")
        self.assertEqual(Packet._safestruct_size, 5)
        self.assertEqual(UserRecord._safestruct_format, "!I16s?")
        self.assertEqual(UserRecord._safestruct_size, 21)
        self.assertEqual(SensorData._safestruct_format, ">Q4IH")
        self.assertEqual(SensorData._safestruct_size, 26)

    def test_field_map_generation(self):
        self.assertIn("status", Header._safestruct_field_map)
        status_validator = Header._safestruct_field_map["status"]["validator"]
        self.assertTrue(status_validator(0))
        self.assertFalse(status_validator(-5))

    def test_non_descriptor_field_raises_error(self):
        with self.assertRaisesRegex(TypeError, "must use a SafeStruct FieldDescriptor"):

            @struct(order=ByteOrder.NETWORK)
            @dataclass
            class BadStruct:
                version: int = 1

    def test_boolean_field_runtime_type_check(self):
        @struct(order=ByteOrder.LITTLE)
        @dataclass
        class BoolTest:
            flag: bool = BooleanField()

        instance = BoolTest(flag=True)
        instance.flag = 1

        with self.assertRaisesRegex(ValidationError, "Validation failed"):
            instance.pack()

    def test_basic_packing(self):
        header = Header(version=5, length=1024, status=1)
        packed_bytes = header.pack()
        expected = stdlib_struct.pack("!BHb", 5, 1024, 1)
        self.assertEqual(packed_bytes, expected)

    def test_packing_validation_error(self):
        bad_header = Header(version=5, length=1024, status=-5)

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'status'"
        ):
            bad_header.pack()

    def test_packing_low_level_error(self):
        @struct(order=ByteOrder.NETWORK)
        @dataclass
        class LowLevelTest:
            value: int = IntField("B")

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'value' in LowLevelTest."
        ):
            LowLevelTest(value=300).pack()

    def test_basic_unpacking(self):
        raw_bytes = stdlib_struct.pack("<?I", True, 0xDEADBEEF)

        packet = Packet.unpack(raw_bytes)
        self.assertIsInstance(packet, Packet)
        self.assertEqual(packet.flag, True)
        self.assertEqual(packet.sequence, 0xDEADBEEF)

    def test_unpacking_buffer_too_small(self):
        raw_bytes_short = b"\x01\x02\x03"

        with self.assertRaisesRegex(UnpackingError, "Expected 4 bytes, got 3"):
            Header.unpack(raw_bytes_short)

    def test_unpacking_struct_error(self):
        raw_bytes_wrong_size = b"\x01\x02\x03\x04\x05\x06"

        with self.assertRaisesRegex(UnpackingError, "Unpacking struct failed"):
            Packet.unpack(raw_bytes_wrong_size)
