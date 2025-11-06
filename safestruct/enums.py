from enum import Enum


class ByteOrder(Enum):
    """
    Mandatory explicit byte order for SafeStruct definitions.
    = Native byte order and size/alignment
    @ Native byte order, standard size, padding may be added
    < Little-endian
    > Big-endian
    ! Network (Big-endian)
    """

    NATIVE = "="
    STANDARD = "@"
    LITTLE = "<"
    BIG = ">"
    NETWORK = "!"

    def to_struct_char(self) -> str:
        return self.value
