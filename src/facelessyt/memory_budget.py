"""Episode 4 executable illustration. NO model is loaded or benchmarked.

Dense, full-context KV tensors only: 2 * layers * KV heads * head dimension *
tokens * sequences * bytes per element. Not valid for all cache architectures.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

GIB = 1024 ** 3


@dataclass(frozen=True)
class Budget:
    capacity_bytes: int = 8 * GIB
    weight_bytes: int = 4 * GIB
    reserve_bytes: int = GIB
    layers: int = 32
    kv_heads: int = 8
    head_dim: int = 128
    cache_bytes_per_element: int = 2
    tokens: int = 8192
    sequences: int = 1


def calculate(budget: Budget) -> dict:
    fields = asdict(budget)
    for name, value in fields.items():
        if type(value) is not int or value < (0 if name == "reserve_bytes" else 1):
            raise ValueError(f"Invalid {name}")
    per_token = 2 * budget.layers * budget.kv_heads * budget.head_dim * budget.cache_bytes_per_element
    cache = per_token * budget.tokens * budget.sequences
    total = budget.weight_bytes + cache + budget.reserve_bytes
    return {"kind": "synthetic_budget_calculation_not_runtime_measurement", "inputs": fields,
        "kv_bytes_per_token_per_sequence": per_token, "cache_bytes": cache,
        "total_budget_bytes": total, "headroom_bytes": budget.capacity_bytes - total,
        "status": "over_budget" if total > budget.capacity_bytes else "under_budget_not_verified",
        "runtime_peak_bytes": None, "tokens_per_second": None,
        "assumptions": ["One shared memory pool; do not add separate RAM and VRAM",
            "Dense full-context KV; no sliding window, compression, offload or prefix sharing",
            "4 GiB resident weights and 1 GiB reserve are illustrative inputs, not measured",
            "Under budget does not prove the runtime will load or meet latency/quality needs"]}


def demo() -> dict:
    return {"schema_version": 1, "label": "ILLUSTRATIVE BUDGET - NOT A HARDWARE BENCHMARK",
        "short": calculate(Budget(tokens=8192)),
        "long": calculate(Budget(tokens=32768)),
        "reduced_context": calculate(Budget(tokens=16384)),
        "two_sequences": calculate(Budget(tokens=16384, sequences=2))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    payload = json.dumps(demo(), indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
