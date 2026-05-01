from typing import List
from collections import Counter
from hashlib import blake2b
import math
import os
import re


VECTOR_DIM = int(os.getenv("RAG_EMBED_DIM", "384"))


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _hash_token(token: str) -> int:
    digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % VECTOR_DIM


def _embed_text(text: str) -> List[float]:
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * VECTOR_DIM

    counts = Counter(tokens)
    vector = [0.0] * VECTOR_DIM

    for token, count in counts.items():
        idx = _hash_token(token)
        weight = 1.0 + math.log(count)
        vector[idx] += weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector

    return [value / norm for value in vector]


def get_embeddings(texts: List[str], model: str = None) -> List[List[float]]:
    """Return deterministic local embeddings that require no external model."""
    if not texts:
        return []

    return [_embed_text(text) for text in texts]
