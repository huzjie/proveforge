# -*- coding: utf-8 -*-
"""Thin, dependency-free hashing helpers (SHA-256 based).

Everything in proveforge is reproducible and built on standard-library hashing:
the same bytes always yield the same digest, on every platform and process.
"""
from __future__ import annotations

import hashlib


def sha256(data: bytes) -> bytes:
    """Return the raw 32-byte SHA-256 digest of ``data``."""
    return hashlib.sha256(data).digest()


def int_to_bytes(value: int, n: int = 8) -> bytes:
    """Encode a non-negative integer as ``n`` little-endian bytes."""
    return int(value).to_bytes(n, "little", signed=False)


def hex_of(data: bytes) -> str:
    """Hex string of a byte digest (for display / transcripts)."""
    return data.hex()
