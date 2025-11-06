import unittest

from safestruct import ValidationError, UnpackingError
from tests.defs import Header


class TestBufferMethods(unittest.TestCase):
    def test_pack_into_with_offset(self):
        """Tests packing into a bytearray with an offset."""
        header_instance = Header(version=1, length=256, status=5)
        buffer = bytearray(b"\xAA" * 10)
        expected_header_bytes = b"\x01\x01\x00\x05"

        offset = 3
        header_instance.pack_into(buffer, offset=offset)

        self.assertEqual(
            buffer[offset : offset + Header._safestruct_size], expected_header_bytes
        )

        self.assertEqual(buffer[:offset], b"\xAA" * offset)
        self.assertEqual(
            buffer[offset + Header._safestruct_size :],
            b"\xAA" * (10 - offset - Header._safestruct_size),
        )

    def test_unpack_from_with_offset(self):
        """Tests unpacking a struct starting from an offset in a bytes object."""

        raw_header_data = b"\x01\x02\x00\x03"
        buffer = b"\xCC\xCC" + raw_header_data + b"\xDD\xDD\xDD\xDD"

        offset = 2

        new_header = Header.unpack_from(buffer, offset=offset)

        self.assertIsInstance(new_header, Header)
        self.assertEqual(new_header.version, 1)
        self.assertEqual(new_header.length, 512)
        self.assertEqual(new_header.status, 3)

    def test_pack_into_validation_check(self):
        """Tests that validation runs before packing into the buffer."""
        bad_header = Header(version=1, length=1, status=-5)
        buffer = bytearray(10)

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'status'"
        ):
            bad_header.pack_into(buffer, offset=0)

    def test_unpack_from_insufficient_buffer_size(self):
        """Tests that size check fires for unpack_from."""
        small_buffer = b"\xAA\xBB\xCC"

        with self.assertRaisesRegex(UnpackingError, "Unpack buffer too small"):
            Header.unpack_from(small_buffer, offset=0)

        buffer_4 = b"\xAA\xBB\xCC\xDD"
        with self.assertRaisesRegex(UnpackingError, "Unpack buffer too small"):
            Header.unpack_from(buffer_4, offset=1)
