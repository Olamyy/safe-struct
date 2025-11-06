# safestruct

A type-safe library for binary packing and unpacking in Python.


# Why?
I was doing some work with sending data over a network in binary format for a streaming engine and was frustrated by the cryptic and error-prone nature of the built-in struct module.

The core issues I'm hoping to solve with these project are:

- Cryptic Errors: Errors are often generic ``struct.error`` exceptions like "unpack requires a buffer of $N$ bytes" or "required argument is not an integer." They provide zero context about which field failed or why, making debugging binary protocols unnecessarily painful.
- No Built-in Validation: If you try to pack a value outside its defined C range (e.g., packing the number `300` into an unsigned byte (`B`), which maxes out at 255), struct fails, but you have no simple hook for adding custom constraints (e.g., checking that a status code is between `1` and `5`).
- Implicit Endianness and Alignment: struct defaults to the host machine's native byte order (`@` prefix) and C-style padding. This means a structure packed on an Intel machine (little-endian) will be read incorrectly on a network system (big-endian) or a different architecture, leading to subtle and devastating cross-platform bugs.
- Positional, Untyped API: Data is packed and unpacked using an ordered tuple based on a terse format string (`!BHb`). This lacks readability and offers no compile-time or runtime type checking against Python's type system (`int`, `bool`, `bytes`).

# How?
safestruct uses the `dataclass` pattern to provide named fields, type hints, and declarative safety while retaining the C-level performance of the underlying struct module.
It does this in a 3-step process:

- Declaration: You define a structure using `@struct` and field descriptors e.g `IntField`, `BytesField`.
- Compilation: The decorator runs *once* at class definition time:
    * It analyzes all field descriptors to build the single, flattened C-compatible format string (e.g., `'!BHb'`).
    * It calculates the total size of the structure.
    * It merges all user-defined checks (e.g., `lambda x: x > 10`) with **mandatory safety checks** (e.g., C-type range limits).
- Method Injection: It injects the high-level methods (`.pack`, `.unpack`, `.pack_into`, `.unpack_from`) which handle validation and complex structure reassembly (nested structs, arrays) before calling the raw `struct` primitives.

It also injects methods for zero-copy memory access around the fastest parts of the standard library:

| Method                         | Description | Performance Feature                                                  |
|:-------------------------------| :--- |:---------------------------------------------------------------------|
| `.pack()`                      | Standard packing. | Validation and flattening done in Python.                            |
| `.pack_into(buffer, offset)`   | Packs into a mutable buffer (`bytearray`). | Zero-copy write: avoids creating and returning a new `bytes` object. |
| `.unpack_from(buffer, offset)` | Unpacks from a memory buffer (`bytes`, `memoryview`). | Zero-copy read: avoids slicing the input buffer before unpacking.    |

Finally, safestruct also provides an introspection API for accessing compiled structure metadata.

| Property | Type | Example Value (for `Header`) | Description |
| :--- | :--- | :--- | :--- |
| **`.format_string`** | `str` | `'!BHb'` | The final, compiled `struct` format string used by the library. |
| **`.size`** | `int` | `4` | The exact total byte size of the structure (no unexpected padding). |
| **`.field_info`** | `dict` | `{'version': {...}, ...}` | Detailed internal metadata, including the raw `struct_char` and validator function for each field. |

## Core Principles

- Explicit over Implicit: Endianness (`LITTLE`, `BIG`, `NETWORK`) is mandatory. Native alignment is forbidden by default.
- Readable and Declarative: Structure is defined using familiar Python dataclasses and named field descriptors (e.g., `IntField`, `BytesField`, `BooleanField`).
- Safe Defaults: Custom validation checks run automatically on packing, and descriptive, contextual exceptions are raised on failure.
- Minimal Overhead: It's a thin wrapper, not a heavy DSL.

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/Olamyy/safestruct
cd safestruct
```

### Install the Package

```bash
uv pip install .
```

### Defining a safe struct
To define a safe struct, add the `@safestruct.struct` decorator to a standard Python `dataclass` and use field descriptors to define each field.

```python
from dataclasses import dataclass
from safestruct import struct, ByteOrder
from safestruct.descriptors import IntField, BytesField, BooleanField

@struct(order=ByteOrder.NETWORK) # MANDATORY explicit byte order
@dataclass
class Header:
    # IntField validates 'int' Python type against 'H' (unsigned short, 2 bytes)
    protocol_version: int = IntField('H')

    # BytesField enforces a fixed length of 16 bytes
    session_id: bytes = BytesField(length=16)

    # BooleanField enforces '?' (1 byte), with custom validation
    is_compressed: bool = BooleanField(check=lambda x: x is True)

```

### Packing and Unpacking
safestruct will automatically compile the format string and injects safe methods, including buffer operations like `pack_into` and `unpack_from` for zero-copy memory handling.


```python

header = Header(
    protocol_version=1024,
    session_id=b'\x01' * 16,
    is_compressed=True
)

# Packing (Validation runs here)
packed_data = header.pack()
# packed_data is bytes, len is 19 bytes (2 + 16 + 1)
print(f"Packed Size: {len(packed_data)} bytes")

# Unpacking (Robust size and type checks run here)
new_header = Header.unpack(packed_data)
print(new_header.protocol_version) # Output: 1024
```

### Error Handling

If you violate a constraint, you get a clear, specific error.

```python
# Example 1: Failing the custom check
bad_header = Header(protocol_version=1, session_id=b'id'*4, is_compressed=False)

try:
    bad_header.pack()
except ValidationError as e:
    # Error message: "Validation failed for field 'is_compressed'. Value: False"
    print(f"Validation Error Caught: {e}")

```
## Lib.struct vs safestruct vs construct

The Python binary packing ecosystem has two main poles:
- The low-level built-in (`Lib.struct`)
- The high-level DSL (`construct`).

safestruct is designed to occupy the safe middle ground. While Construct solves many of the safety issues with struct, it introduces its own powerful but complex DSL. This makes it overkill for simple, fixed-layout protocols and introduces performance overhead.

**SafeStruct is not a replacement for Construct**. If you need dynamic arrays, conditional parsing, or complex bit-level manipulation, Construct is the better choice. If you just need a safe, fast, fixed-size C struct equivalent in Python, safestruct is the answer.


```markdown
| Feature            | struct (Built-in)                | construct          | SafeStruct                       |
|--------------------|----------------------------------|------------------------------------|---------------------------------------------|
| Interface          | Format Strings (`'!ih'`)         | Custom DSL (`Struct("h" / Int16ub)`) | Python Dataclasses                          |
| Endianness         | Implicit (Native Default)        | Optional, Explicit                 | Mandatory, Explicit                         |
| Alignment/Padding  | Implicit (C-style)               | Fully Customizable                 | Explicitly Disabled by Default (Safety)     |
| Named Fields       | No (Tuple Output)                | Yes (via DSL)                      | Yes (Dataclass fields)                      |
| Type Safety        | None                             | Limited (via DSL types)            | Strong (Python Type Hints + Descriptors)    |
| Custom Validation  | Manual boilerplate required       | Yes (via specialized constructs)   | Simple check lambda in Field                |
| Performance        | Fastest (C-speed)                | Medium (Python object overhead)    | Near-C Speed (relies on struct core)        |
```

### Side-by-Side Code Example

Let's consider a simple network header structure with three fields to illustrate the differences.
The structure contains:
- `version`: Unsigned Char (B / 1 byte)
- `length`: Unsigned Short (H / 2 bytes)
- `status`: Signed Char (b / 1 byte)


#### Struct Definition

- ``Lib.struct (Format String)``: No explicit definition
  - The format string is the only definition: '!BHb'
  - This format string must be remembered and reused manually.

- ``safestruct`` : Clear and Type-Safe

  ```python
  from dataclasses import dataclass
  from safestruct import struct, ByteOrder
  from safestruct.descriptors import IntField

  @struct(order=ByteOrder.NETWORK)
  @dataclass
  class Header:
      version: int = IntField('B')
      length: int = IntField('H')
      status: int = IntField('b')

  ```

- `construct` : DSL required

  ```python
  from construct import Struct, Int8ub, Int16ub, Int8sb

  Header = Struct(
      "version" / Int8ub,
      "length" / Int16ub,
      "status" / Int8sb
  )
  ````

#### Packing

- struct : Positional and Ambiguous

  ```python
  import struct

  # Need to ensure the values (1, 1024, -1) are in the
  # exact positional order of the format string ('B', 'H', 'b').
  packed_data = struct.pack('!BHb', 1, 1024, -1)
  ```

- `safestruct`: Named and Validated

  ```python


  # Readable instance creation
  header = Header(version=1, length=1024, status=-1)

  # Packing uses the injected method
  packed_data = header.pack()
  ```

- construct: DSL-based Build

  ```python
  # Building requires a specific build dictionary or container
  packed_data = Header.build(
      dict(version=1, length=1024, status=-1)
  )
  ```

#### Unpacking and Debugging

- struct : Ambiguous Tuple Output
  ```python


  # Output is a tuple: (1, 1024, -1)
  values = struct.unpack('!BHb', packed_data)

  # Manual assignment is required, prone to error if structure changes
  version, length, status = values

  # Debugging Size Mismatch: "unpack requires a buffer of 4 bytes"
  # The error gives no context about the Header structure.
  ```

- safestruct : Named Instance Output and Clear Errors

  ```python


    # Output is a named instance (type Header)
    new_header = header.unpack(packed_data)

    # Access is clear and type-hinted
    print(f"Status: {new_header.status}")

    # Debugging Size Mismatch:
    # Raises UnpackingError: "Unpack buffer too small for Header. Expected 4 bytes, got 3."

    ```

- construct : Container Output and Clear Errors

  ```python


  # Output is a named container object
  new_header = Header.parse(packed_data)

  # Access is clear
  print(f"Status: {new_header.status}")

  # Debugging: Construct raises its own specific exceptions with full context.
  ```
