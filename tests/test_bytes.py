import unittest
import struct as stdlib_struct
from safestruct import ValidationError, FormatError
from safestruct import BytesField
from tests.defs import ProtocolMessage


class TestBytes(unittest.TestCase):
    def test_bytes_field_packing_length_error(self):
        msg_too_long = ProtocolMessage(magic=1, id=b"DATAA", reserved=b"\x00")

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'id'"
        ):
            msg_too_long.pack()

        msg_wrong_value = ProtocolMessage(magic=1, id=b"DATA", reserved=b"\x01")

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'reserved'"
        ):
            msg_wrong_value.pack()

    def test_bytes_field_unpacking(self):
        raw_bytes = stdlib_struct.pack("<H4s1s", 0xBEEF, b"TEST", b"\xFF")

        msg = ProtocolMessage.unpack(raw_bytes)
        self.assertIsInstance(msg.id, bytes)
        self.assertEqual(msg.id, b"TEST")
        self.assertEqual(msg.reserved, b"\xFF")

    def test_bytes_field_init_validation(self):
        with self.assertRaisesRegex(FormatError, "positive integer 'length'"):
            BytesField(length=0)
