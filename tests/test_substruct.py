import unittest
import struct as stdlib_struct
from dataclasses import dataclass

from safestruct import FormatError
from safestruct import SubStructField
from tests.defs import SubStructMessage, Header


class TestSubStructField(unittest.TestCase):
    def test_nested_format_compilation(self):
        self.assertEqual(Header._safestruct_format, "!BHb")
        self.assertEqual(SubStructMessage._safestruct_format, "<BHbL")
        self.assertEqual(SubStructMessage._safestruct_size, 8)

    def test_substruct_packing(self):
        header_instance = Header(version=1, length=1024, status=1)
        message_instance = SubStructMessage(
            header=header_instance, payload_id=0xDEADBEEF
        )
        packed_data = message_instance.pack()
        self.assertEqual(len(packed_data), 8)
        expected_data = stdlib_struct.pack("<BHbL", 1, 1024, 1, 0xDEADBEEF)
        self.assertEqual(packed_data, expected_data)

    def test_substruct_unpacking(self):
        raw_data = stdlib_struct.pack("<BHbL", 5, 2048, 1, 0xCAFEF00D)

        message = SubStructMessage.unpack(raw_data)

        self.assertIsInstance(message, SubStructMessage)
        self.assertIsInstance(message.header, Header)
        self.assertEqual(message.header.version, 5)
        self.assertEqual(message.header.length, 2048)
        self.assertEqual(message.header.status, 1)
        self.assertEqual(message.payload_id, 0xCAFEF00D)

    def test_substruct_raises_on_non_safestruct_class(self):
        @dataclass
        class UnsafeHeader:
            a: int

        with self.assertRaisesRegex(FormatError, "is not a valid SafeStruct"):
            SubStructField(UnsafeHeader)
