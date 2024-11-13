from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nrk_psapi.auth.models import HashingAlgorithm


def get_n(log_n):
    """Get 2^logN."""
    return (1 << log_n) & 0xFFFFFFFF


def parse_hashing_algorithm(algorithm: str | None) -> HashingAlgorithm:
    """Parse hashing algorithm string, like 'cscrypt:17:8:1:32'."""
    default_algorithm = {"algorithm": "cleartext"}
    if algorithm is None:
        return default_algorithm
    if "cscrypt" not in algorithm:
        return default_algorithm
    parts = algorithm.split(":")
    if len(parts) < 5:  # noqa: PLR2004
        return default_algorithm

    return {
        "algorithm": "cscrypt",
        "n": get_n(int(parts[1])),
        "r": int(parts[2]),
        "p": int(parts[3]),
        "dkLen": int(parts[4]),
    }
