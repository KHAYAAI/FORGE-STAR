"""CCSDS convolutional code (131.0-B): K=7, rate 1/2, G1=171o, G2=133o with G2 output inverted.

Inner code of the CCSDS concatenated scheme: Reed–Solomon (outer, forgestar/fec.py) then this code.
About 3 dB more margin than RS alone. Encoder here and in flight/libforge (forge_conv_encode);
soft-decision Viterbi decoder for the gateway.

Bit/symbol convention: input bits MSB first; for each bit two output symbols (G1, then not-G2).
A 6-bit zero tail flushes the encoder. Soft symbols for the decoder: +1 means bit 0, -1 means bit 1
(the BPSK mapping in forgestar/modem.py), any real-valued confidence.
"""
from __future__ import annotations

import numpy as np

K = 7
G1, G2 = 0o171, 0o133
NSTATE = 1 << (K - 1)


def _parity(x: int) -> int:
    return bin(x).count("1") & 1


# output symbols for (state, input bit): register = (bit << 6) | state, newest bit in the MSB
_OUT = np.zeros((NSTATE, 2, 2), dtype=np.uint8)
for _s in range(NSTATE):
    for _b in (0, 1):
        reg = (_b << (K - 1)) | _s
        _OUT[_s, _b, 0] = _parity(reg & G1)
        _OUT[_s, _b, 1] = _parity(reg & G2) ^ 1      # CCSDS: G2 symbol inverted


def encode_bits(bits: np.ndarray) -> np.ndarray:
    bits = np.concatenate([np.asarray(bits, dtype=np.uint8), np.zeros(K - 1, np.uint8)])   # zero tail
    out = np.empty(2 * len(bits), np.uint8)
    s = 0
    for i, b in enumerate(bits):
        out[2 * i], out[2 * i + 1] = _OUT[s, b]
        s = ((b << (K - 1)) | s) >> 1
    return out


def encode(data: bytes) -> np.ndarray:
    return encode_bits(np.unpackbits(np.frombuffer(data, dtype=np.uint8)))


# trellis: next state and the two predecessor states of each state
_NEXT = np.array([[((b << (K - 1)) | s) >> 1 for b in (0, 1)] for s in range(NSTATE)])
_PREV = [[] for _ in range(NSTATE)]
for _s in range(NSTATE):
    for _b in (0, 1):
        _PREV[_NEXT[_s, _b]].append((_s, _b))
_P0 = np.array([p[0][0] for p in _PREV]); _B0 = np.array([p[0][1] for p in _PREV])
_P1 = np.array([p[1][0] for p in _PREV]); _B1 = np.array([p[1][1] for p in _PREV])
# expected BPSK symbols (+1 for 0, -1 for 1) on each incoming branch
_E0 = 1.0 - 2.0 * _OUT[_P0, _B0].astype(float)     # (NSTATE, 2)
_E1 = 1.0 - 2.0 * _OUT[_P1, _B1].astype(float)


def viterbi(soft: np.ndarray, tail: bool = True) -> tuple[np.ndarray, float]:
    """Soft symbols (2 per bit) -> decoded bits (tail removed) and the final path metric (higher = better)."""
    soft = np.asarray(soft, dtype=float)
    n = len(soft) // 2
    pm = np.full(NSTATE, -1e18); pm[0] = 0.0
    dec = np.empty((n, NSTATE), dtype=np.uint8)
    for i in range(n):
        r = soft[2 * i:2 * i + 2]
        m0 = pm[_P0] + _E0 @ r
        m1 = pm[_P1] + _E1 @ r
        choose1 = m1 > m0
        dec[i] = choose1
        pm = np.where(choose1, m1, m0)
    s = 0 if tail else int(np.argmax(pm))
    metric = float(pm[s])
    bits = np.empty(n, np.uint8)
    for i in range(n - 1, -1, -1):
        c = dec[i, s]
        bits[i] = _B1[s] if c else _B0[s]
        s = _P1[s] if c else _P0[s]
    return (bits[:-(K - 1)] if tail else bits), metric
