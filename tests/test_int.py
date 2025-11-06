import unittest
from dataclasses import dataclass

from safestruct import struct
from safestruct import ValidationError
from safestruct import IntField
from safestruct.enums import ByteOrder


class TestIntField(unittest.TestCase):
    def test_int_field_packing_range_overflow_error(self):
        @struct(order=ByteOrder.NETWORK)
        @dataclass
        class RangeTest:
            value: int = IntField("B")

        instance = RangeTest(value=256)

        with self.assertRaisesRegex(
            ValidationError,
            "Validation failed for field 'value' in RangeTest. Value: 256",
        ):
            instance.pack()

    def test_int_field_packing_range_underflow_error(self):
        @struct(order=ByteOrder.NETWORK)
        @dataclass
        class RangeTest:
            value: int = IntField("B")

        with self.assertRaisesRegex(
            ValidationError,
            "Validation failed for field 'value' in RangeTest. Value: -1",
        ):
            RangeTest(value=-1).pack()

    def test_int_field_packing_range_signed_underflow(self):
        @struct(order=ByteOrder.NETWORK)
        @dataclass
        class RangeTest:
            value: int = IntField("h")

        with self.assertRaisesRegex(
            ValidationError,
            "Validation failed for field 'value' in RangeTest. Value: -32769",
        ):
            RangeTest(value=-32769).pack()

    def test_int_field_packing_range_success(self):
        """Test successful packing when value is exactly on the boundary (0 and 255)."""

        @struct(order=ByteOrder.NETWORK)
        @dataclass
        class RangeTest:
            value: int = IntField("B")

        instance_max = RangeTest(value=255)
        expected_size = RangeTest._safestruct_size
        packed_data = instance_max.pack()
        self.assertEqual(len(packed_data), expected_size)
