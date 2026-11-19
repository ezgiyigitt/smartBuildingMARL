"""Grouped split protocol for ASHRAE rows. Never split only by row index."""

from __future__ import annotations

import hashlib


def assign_group(group_id: object, seed: int = 0) -> str:
    digest = hashlib.sha256(f"{seed}:{group_id}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"
