import timeit
import struct as stdlib_struct
from dataclasses import dataclass
from typing import List

from construct import Struct as ConStruct, Int64ub, Int32ub, Int16ub, Array as ConArray

from safestruct.core import struct
from safestruct.enums import ByteOrder
from safestruct.descriptors import IntField, ArrayField

NUM_ITERATIONS = 100_000_000
DATA_VALUES = (1678886400, [10, 20, 30, 40], 0xABCD)


@struct(order=ByteOrder.BIG)
@dataclass
class SafeSensorData:
    timestamp: int = IntField("Q")
    readings: List[int] = ArrayField(IntField("I"), count=4)
    checksum: int = IntField("H")


safe_struct_instance = SafeSensorData(
    timestamp=DATA_VALUES[0], readings=DATA_VALUES[1], checksum=DATA_VALUES[2]
)

RAW_FORMAT = ">Q4IH"
RAW_PACK_VALUES = (DATA_VALUES[0], *DATA_VALUES[1], DATA_VALUES[2])
RAW_PACKED_DATA = stdlib_struct.pack(RAW_FORMAT, *RAW_PACK_VALUES)

ConstructSensorData = ConStruct(
    "timestamp" / Int64ub, "readings" / ConArray(4, Int32ub), "checksum" / Int16ub
)
CONSTRUCT_BUILD_DATA = {
    "timestamp": DATA_VALUES[0],
    "readings": DATA_VALUES[1],
    "checksum": DATA_VALUES[2],
}
CONSTRUCT_PACKED_DATA = ConstructSensorData.build(CONSTRUCT_BUILD_DATA)


def benchmark_safestruct_pack():
    safe_struct_instance.pack()


def benchmark_safestruct_unpack():
    SafeSensorData.unpack(RAW_PACKED_DATA)


def benchmark_raw_struct_pack():
    stdlib_struct.pack(RAW_FORMAT, *RAW_PACK_VALUES)


def benchmark_raw_struct_unpack():
    stdlib_struct.unpack(RAW_FORMAT, RAW_PACKED_DATA)


def benchmark_construct_build():
    ConstructSensorData.build(CONSTRUCT_BUILD_DATA)


def benchmark_construct_parse():
    ConstructSensorData.parse(CONSTRUCT_PACKED_DATA)


def run_benchmark(func, label):
    """Executes a function and reports the total time."""
    print(f"Running benchmark for {label} ({NUM_ITERATIONS} iterations)...")

    start_time = timeit.default_timer()
    for _ in range(NUM_ITERATIONS):
        func()
    end_time = timeit.default_timer()

    total_time = end_time - start_time
    time_per_op = total_time / NUM_ITERATIONS * 1e6

    print(f"  Total Time: {total_time:.4f} seconds")
    print(f"  Time per Op: {time_per_op:.2f} µs\n")
    return time_per_op


def main():
    print("--- SafeStruct Performance Benchmarks ---")

    print("\n[UNPACKING / PARSING]")
    raw_time_u = run_benchmark(benchmark_raw_struct_unpack, "1. Raw struct.unpack")
    safe_time_u = run_benchmark(benchmark_safestruct_unpack, "2. SafeStruct.unpack")
    construct_time_u = run_benchmark(benchmark_construct_parse, "3. Construct.parse")

    print("\n[PACKING / BUILDING]")
    raw_time_p = run_benchmark(benchmark_raw_struct_pack, "1. Raw struct.pack")
    safe_time_p = run_benchmark(benchmark_safestruct_pack, "2. SafeStruct.pack")
    construct_time_p = run_benchmark(benchmark_construct_build, "3. Construct.build")

    print("\n--- Summary Comparison (Time per Operation in µs) ---")
    print("| Operation | Raw struct | safestruct | Construct |")
    print("|:----------|-----------:|-----------:|----------:|")

    safe_overhead_u = (safe_time_u - raw_time_u) / raw_time_u * 100 if raw_time_u else 0
    construct_overhead_u = (
        (construct_time_u - raw_time_u) / raw_time_u * 100 if raw_time_u else 0
    )
    print(
        f"| UNPACKING | {raw_time_u:.2f} µs | {safe_time_u:.2f} µs ({safe_overhead_u:.0f}% overhead) | {construct_time_u:.2f} µs ({construct_overhead_u:.0f}% overhead)\n"
    )

    safe_overhead_p = (safe_time_p - raw_time_p) / raw_time_p * 100 if raw_time_p else 0
    print(
        f"| PACKING   | {raw_time_p:.2f} µs | {safe_time_p:.2f} µs ({safe_overhead_p:.0f}% overhead) | {construct_time_p:.2f} µs ({construct_overhead_u:.0f}% overhead)\n"
    )


if __name__ == "__main__":
    main()
