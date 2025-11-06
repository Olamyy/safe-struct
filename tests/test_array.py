import unittest
import struct as stdlib_struct

from safestruct import ValidationError, FormatError
from safestruct import SubStructField
from safestruct.descriptors import TextField, ArrayField
from tests.defs import SensorData, Header


class TestArrayField(unittest.TestCase):
    def test_array_field_packing(self):
        """Test successful packing of fields including the array."""
        data = SensorData(
            timestamp=1678886400, readings=[10, 20, 30, 40], checksum=0xF001
        )
        packed = data.pack()
        expected = stdlib_struct.pack(">QIIIIH", 1678886400, 10, 20, 30, 40, 0xF001)

        self.assertEqual(packed, expected)
        self.assertEqual(len(packed), 26)

    def test_array_field_unpacking(self):
        raw_data = stdlib_struct.pack(">QIIIIH", 1678886401, 100, 200, 300, 400, 0xEF01)

        data = SensorData.unpack(raw_data)

        self.assertIsInstance(data.readings, list)
        self.assertEqual(data.readings, [100, 200, 300, 400])
        self.assertEqual(data.timestamp, 1678886401)
        self.assertEqual(data.checksum, 0xEF01)

    def test_array_field_packing_size_validation(self):
        data_bad_size = SensorData(timestamp=1, readings=[10, 20, 30], checksum=1)

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'readings'"
        ):
            data_bad_size.pack()

    def test_array_field_packing_type_validation(self):
        data_bad_type = SensorData(timestamp=1, readings=[10, "20", 30, 40], checksum=1)

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'readings'"
        ):
            data_bad_type.pack()

    def test_array_field_format_validation(self):
        with self.assertRaisesRegex(
            FormatError, "currently only supports IntField or BooleanField primitives"
        ):
            ArrayField(TextField(length=10), count=5)

        with self.assertRaisesRegex(
            FormatError, "currently only supports IntField or BooleanField primitives"
        ):
            ArrayField(SubStructField(Header), count=2)
