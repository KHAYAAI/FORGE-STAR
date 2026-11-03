"""Software BPSK modem for the FORGE STAR downlink: complex baseband samples <-> link-block bytes.

Transmit: bytes -> bits (MSB first) -> BPSK symbols -> root-raised-cosine pulses (SPS samples/symbol).
Receive (what a gateway SDR / SatNOGS recording goes through):
  1. coarse frequency: squaring removes BPSK modulation, FFT peak at 2*offset -> derotate
  2. matched RRC filter
  3. symbol timing: pick the sample phase with the most energy (Gardner-free, fine for short bursts)
  4. carrier phase/residual frequency: decision-directed PLL
  5. bits -> bytes; the 180° BPSK ambiguity is resolved by finding the ASM (or its inverse)
The bytes then go to forgestar.fec.decode_stream. numpy only.
"""
from __future__ import annotations

import numpy as np

from .fec import ASM

SPS = 8          # samples per symbol
ROLLOFF = 0.35
SPAN = 8         # filter span in symbols


def rrc(sps: int = SPS, beta: float = ROLLOFF, span: int = SPAN) -> np.ndarray:
    t = np.arange(-span * sps // 2, span * sps // 2 + 1) / sps
    h = np.zeros_like(t)
    for i, x in enumerate(t):
        if abs(x) < 1e-9:
            h[i] = 1 - beta + 4 * beta / np.pi
        elif abs(abs(4 * beta * x) - 1) < 1e-9:
            h[i] = beta / np.sqrt(2) * ((1 + 2 / np.pi) * np.sin(np.pi / (4 * beta)) + (1 - 2 / np.pi) * np.cos(np.pi / (4 * beta)))
        else:
            h[i] = (np.sin(np.pi * x * (1 - beta)) + 4 * beta * x * np.cos(np.pi * x * (1 + beta))) / (np.pi * x * (1 - (4 * beta * x) ** 2))
    return h / np.sqrt(np.sum(h ** 2))


_H = rrc()


def modulate(data: bytes, preamble_bytes: int = 16) -> np.ndarray:
    """Bytes -> complex baseband. A 0x55 preamble helps the receiver settle before the ASM."""
    bits = np.unpackbits(np.frombuffer(b"\x55" * preamble_bytes + data + b"\x00" * 4, dtype=np.uint8))
    sym = 1.0 - 2.0 * bits                     # 0 -> +1, 1 -> -1
    up = np.zeros(len(sym) * SPS); up[::SPS] = sym
    return np.convolve(up, _H).astype(np.complex128)


def channel(x: np.ndarray, ebn0_db: float, freq_offset: float = 0.0, phase: float = 0.0,
            delay: int = 0, rng: np.random.Generator | None = None) -> np.ndarray:
    """AWGN at Eb/N0 (signal energy per bit measured from x), plus frequency offset (cycles/sample),
    carrier phase and sample delay."""
    rng = rng or np.random.default_rng(0)
    y = np.concatenate([np.zeros(delay, complex), x])
    n = np.arange(len(y))
    y = y * np.exp(1j * (2 * np.pi * freq_offset * n + phase))
    eb = np.sum(np.abs(x) ** 2) / (len(x) / SPS)          # energy per BPSK symbol = per bit
    n0 = eb / (10 ** (ebn0_db / 10))
    return y + np.sqrt(n0 / 2) * (rng.standard_normal(len(y)) + 1j * rng.standard_normal(len(y)))


def demodulate(y: np.ndarray, max_offset: float = 0.02) -> bytes:
    """Complex baseband -> byte stream (BPSK ambiguity resolved via the ASM)."""
    # 1. coarse frequency offset from the squared signal
    sq = y ** 2
    nfft = 1 << int(np.ceil(np.log2(len(sq) * 4)))
    spec = np.abs(np.fft.fft(sq, nfft))
    freqs = np.fft.fftfreq(nfft)
    band = np.abs(freqs) <= 2 * max_offset
    f2 = freqs[band][np.argmax(spec[band])]
    y = y * np.exp(-1j * np.pi * f2 * np.arange(len(y)))      # remove f2/2
    # 2. matched filter
    z = np.convolve(y, _H)
    # 3. timing: phase with the most energy
    best = max(range(SPS), key=lambda k: np.sum(np.abs(z[k::SPS]) ** 2))
    s = z[best::SPS]
    # 4. decision-directed PLL (second order)
    out = np.empty(len(s), complex); ph, fr = 0.0, 0.0
    a, b = 0.05, 0.002
    for i, v in enumerate(s):
        r = v * np.exp(-1j * ph); out[i] = r
        err = np.sign(r.real) * r.imag
        fr += b * err; ph += fr + a * err
    bits = (out.real < 0).astype(np.uint8)
    # 5. bytes, both polarities; keep the one containing the ASM
    asm_bits = np.unpackbits(np.frombuffer(ASM, dtype=np.uint8))
    best_stream, best_score = b"", -1
    for inv in (0, 1):
        bb = bits ^ inv
        corr = np.correlate(1 - 2 * bb.astype(float), 1 - 2 * asm_bits.astype(float), mode="valid")
        k = int(np.argmax(corr))
        score = corr[k]
        aligned = bb[k % 8:]
        stream = np.packbits(aligned[: len(aligned) // 8 * 8]).tobytes()
        if score > best_score:
            best_score, best_stream = score, stream
    return best_stream
