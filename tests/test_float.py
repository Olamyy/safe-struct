import unittest
import struct as std_struct
from safestruct.core import ValidationError, FormatError
from safestruct.descriptors import FloatField
from tests.defs import TelemetryPacket


class TestFloatField(unittest.TestCase):
    def test_float_field_format_validation(self):
        """Tests that FloatField only accepts 'f' or 'd' codes."""
        FloatField("f")
        FloatField("d")
        FloatField("<d")

        with self.assertRaisesRegex(FormatError, "not a valid float format char"):
            FloatField("H")

        with self.assertRaisesRegex(FormatError, "not a valid float format char"):
            FloatField("s")

    def test_float_field_packing_success(self):
        """Tests successful packing of Float32 and Float64."""

        TS = 1700000000
        TEMP = 25.5
        PRES = 101325.456

        packet = TelemetryPacket(
            timestamp=TS, temperature=TEMP, pressure=PRES, is_valid=True
        )

        packed_data = packet.pack()

        self.assertEqual(len(packed_data), 21)

        expected = std_struct.pack("<Qfdb", TS, TEMP, PRES, True)
        self.assertEqual(packed_data, expected)

    def test_float_field_unpacking_success(self):
        """Tests successful unpacking of Float32 and Float64."""
        timestamp = 1700000000
        temperature = 25.5
        pressure = 101325.456

        raw_data = std_struct.pack("<Qfdb", timestamp, temperature, pressure, False)

        packet = TelemetryPacket.unpack(raw_data)

        self.assertIsInstance(packet, TelemetryPacket)
        self.assertIsInstance(packet.temperature, float)

        self.assertAlmostEqual(packet.temperature, temperature, places=6)
        self.assertAlmostEqual(packet.pressure, pressure, places=9)

    def test_float_field_packing_type_error(self):
        """Tests that attempting to pack a non-float type raises ValidationError."""

        packet_bad = TelemetryPacket(
            timestamp=1, temperature="25.5", pressure=100000.0, is_valid=False
        )

        with self.assertRaisesRegex(
            ValidationError, "Validation failed for field 'temperature'"
        ):
            packet_bad.pack()
