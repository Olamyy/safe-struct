import unittest
import struct as stdlib_struct

from safestruct import ValidationError
from tests.defs import UserRecord


class TestSafeStructCore(unittest.TestCase):
    def test_text_field_packing_padding_and_encoding(self):
        user = UserRecord(user_id=123, username="Alice", is_admin=True)
        packed = user.pack()

        self.assertEqual(len(packed), 21)

        expected_name_bytes = b"Alice" + (b"\x00" * 11)

        expected = stdlib_struct.pack("!I16s?", 123, expected_name_bytes, True)
        self.assertEqual(packed, expected)

    def test_text_field_unpacking_stripping_and_decoding(self):
        raw_name = b"Bob" + (b"\x00" * 13)
        raw_data = stdlib_struct.pack("!I16s?", 456, raw_name, False)

        user = UserRecord.unpack(raw_data)

        self.assertIsInstance(user.username, str)
        self.assertEqual(user.username, "Bob")
        self.assertEqual(user.user_id, 456)
        self.assertEqual(user.is_admin, False)

    def test_text_field_packing_length_validation(self):
        long_name = "A_very_long_username_over_16_chars"

        user_too_long = UserRecord(user_id=1, username=long_name, is_admin=False)

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'username'"
        ):
            user_too_long.pack()
