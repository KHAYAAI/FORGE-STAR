"""Radio link layer for FORGE STAR downlinks: error correction, randomising and sync.

Wraps one store-and-forward frame (forgestar.frames v1) into a link block:

    ASM 0x1ACFFC1D | codeword 1 | codeword 2 | ... | codeword N        (randomised after the ASM)

Each codeword is Reed–Solomon (255,223) with CCSDS parameters (field polynomial
x^8+x^7+x^2+x+1, generator roots β^112..β^143 with β = α^11). It corrects up to
16 wrong bytes per codeword. The first codeword's data starts with a 3-byte header:
u16 frame length and u8 codeword count. The last codeword is zero-padded (virtual fill).

The pseudo-randomiser is the CCSDS sequence h(x) = x^8+x^7+x^5+x^3+1 (seed all ones),
restarted after every ASM. It guarantees bit transitions for the receiver's clock recovery.

Note: this uses the conventional symbol basis. Real CCSDS RS uses the dual basis. Before
interoperating with third-party CCSDS ground stations, add the basis transform (a
fixed 8×8 bit matrix) on both ends. Our own satellite and gateway match each other.

The flight side only needs `encode_block` (implemented again in C in flight/libforge);
the ground uses `decode_stream`. Both are pure Python with no dependencies. The tests check
the encoder against the reedsolo package and the decoder against random error patterns.
"""
from __future__ import annotations

import struct

ASM = bytes.fromhex("1ACFFC1D")
N, K = 255, 223
NSYM = N - K
PRIM, FCR, GEN = 0x187, 112, 11

# --- GF(2^8) tables ---
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x; LOG[_x] = _i
    _x <<= 1
    if _x & 0x100: _x ^= PRIM
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gmul(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def _generator() -> list[int]:
    g = [1]
    for j in range(FCR, FCR + NSYM):
        root = EXP[(GEN * j) % 255]
        g = [c ^ gmul(root, p) for c, p in zip(g + [0], [0] + g)]  # g(x) * (x + root)
    return g[::-1]  # highest degree first, monic


GPOLY = _generator()


def rs_encode(data: bytes) -> bytes:
    """Systematic RS(255,223): returns data (223 bytes) + 32 parity bytes."""
    if len(data) != K:
        raise ValueError("RS block must be 223 bytes")
    par = [0] * NSYM
    for byte in data:
        fb = byte ^ par[0]
        par = par[1:] + [0]
        if fb:
            for i in range(NSYM):
                par[i] ^= gmul(fb, GPOLY[i + 1])
    return bytes(data) + bytes(par)


class RSDecodeError(ValueError):
    pass


def _poly_eval(p: list[int], x: int) -> int:
    y = 0
    for c in p:
        y = gmul(y, x) ^ c
    return y


def rs_decode(cw: bytes) -> tuple[bytes, int]:
    """Decode one RS(255,223) codeword. Returns (223 data bytes, number of bytes corrected).

    Syndromes -> Berlekamp–Massey (error locator) -> Chien search -> Forney (magnitudes).
    Raises RSDecodeError when more than 16 bytes are wrong (detected, not miscorrected,
    in the vast majority of cases)."""
    if len(cw) != N:
        raise ValueError("codeword must be 255 bytes")
    c = list(cw)
    roots = [EXP[(GEN * j) % 255] for j in range(FCR, FCR + NSYM)]
    synd = [_poly_eval(c, r) for r in roots]
    if not any(synd):
        return bytes(c[:K]), 0
    # Berlekamp–Massey over S_0..S_31; locator polynomial stored lowest degree first
    lam, b, L, m, bb = [1] + [0] * NSYM, [1] + [0] * NSYM, 0, 1, 1
    for n in range(NSYM):
        d = synd[n]
        for i in range(1, L + 1):
            d ^= gmul(lam[i], synd[n - i])
        if d == 0:
            m += 1
        elif 2 * L <= n:
            t = lam[:]
            coef = gmul(d, EXP[255 - LOG[bb]])
            for i in range(NSYM + 1 - m):
                lam[i + m] ^= gmul(coef, b[i])
            L, b, bb, m = n + 1 - L, t, d, 1
        else:
            coef = gmul(d, EXP[255 - LOG[bb]])
            for i in range(NSYM + 1 - m):
                lam[i + m] ^= gmul(coef, b[i])
            m += 1
    lam = lam[:L + 1]
    if L > NSYM // 2:
        raise RSDecodeError("too many errors")
    # Chien search: position p (0 = first byte) has locator X = β^(N-1-p); root at X^-1
    beta_log = GEN % 255
    pos = []
    for p in range(N):
        e = (beta_log * (N - 1 - p)) % 255
        xinv = EXP[(255 - e) % 255]
        y = 0
        for coefi in reversed(lam):
            y = gmul(y, xinv) ^ coefi
        if y == 0:
            pos.append((p, e))
    if len(pos) != L:
        raise RSDecodeError("too many errors (locator roots mismatch)")
    # Forney: Ω(x) = S(x)Λ(x) mod x^32, magnitude = X^(1-FCR) Ω(X^-1) / Λ'(X^-1)
    S = synd
    omega = [0] * NSYM
    for i in range(NSYM):
        for j in range(min(i, L) + 1):
            omega[i] ^= gmul(S[i - j], lam[j])
    for p, e in pos:
        xinv = EXP[(255 - e) % 255]
        om = 0
        for coefi in reversed(omega):
            om = gmul(om, xinv) ^ coefi
        dl = 0  # formal derivative of Λ at X^-1: odd terms only
        for i in range(1, L + 1, 2):
            dl ^= gmul(lam[i], EXP[(LOG[xinv] * (i - 1)) % 255]) if lam[i] else 0
        if dl == 0:
            raise RSDecodeError("Forney denominator zero")
        xpow = EXP[(e * (1 - FCR)) % 255]
        c[p] ^= gmul(xpow, gmul(om, EXP[255 - LOG[dl]]))
    if any(_poly_eval(c, r) for r in roots):
        raise RSDecodeError("correction failed")
    return bytes(c[:K]), len(pos)


def pn_sequence(n: int) -> bytes:
    """CCSDS pseudo-random sequence (CCSDS 131.0-B): h(x)=x^8+x^7+x^5+x^3+1, all-ones seed.
    Starts FF 48 0E C0 9A 0D 70 BC. Shift register r[0..7]; output r[0]; feedback r0^r3^r5^r7."""
    reg, out = [1] * 8, bytearray()
    for _ in range(n):
        byte = 0
        for _ in range(8):
            byte = (byte << 1) | reg[0]
            fb = reg[0] ^ reg[3] ^ reg[5] ^ reg[7]
            reg = reg[1:] + [fb]
        out.append(byte)
    return bytes(out)


_PN = pn_sequence(255 * 20)


def randomise(b: bytes) -> bytes:
    if len(b) > len(_PN):
        raise ValueError("block too long")
    return bytes(x ^ y for x, y in zip(b, _PN))


def encode_block(frame: bytes) -> bytes:
    """One v1 frame -> one link block (ASM + randomised RS codewords)."""
    n_cw = -(-(len(frame) + 3) // K)
    if n_cw > 20:
        raise ValueError("frame too large for one link block (max 20 codewords)")
    payload = struct.pack(">HB", len(frame), n_cw) + frame
    payload += bytes(n_cw * K - len(payload))
    cws = b"".join(rs_encode(payload[i * K:(i + 1) * K]) for i in range(n_cw))
    return ASM + randomise(cws)


def _asm_positions(stream: bytes, max_bit_errors: int = 3):
    target = int.from_bytes(ASM, "big")
    i = 0
    while i + 4 <= len(stream):
        if bin(int.from_bytes(stream[i:i + 4], "big") ^ target).count("1") <= max_bit_errors:
            yield i
        i += 1


def decode_stream(stream: bytes):
    """Find link blocks in a received byte stream and return (frames, stats).

    Tolerates noise before/between blocks, up to 3 bit errors in the ASM and up to
    16 byte errors per codeword. Unrecoverable blocks are counted, not raised."""
    frames, stats = [], {"blocks": 0, "corrected_bytes": 0, "failed": 0}
    pos, end = 0, len(stream)
    for p in _asm_positions(stream):
        if p < pos:
            continue
        body = stream[p + 4:]
        if len(body) < N:
            break

        try:
            first = randomise(body[:N])
            msg, fixed = rs_decode(first)
            flen, n_cw = struct.unpack(">HB", msg[:3])
            if not 1 <= n_cw <= 20 or len(body) < n_cw * N or flen > n_cw * K - 3:
                raise RSDecodeError("bad header")
            der = randomise(body[:n_cw * N])
            data = bytearray(msg)
            for i in range(1, n_cw):
                m, e = rs_decode(der[i * N:(i + 1) * N]); data += m; fixed += e
            frames.append(bytes(data[3:3 + flen]))
            stats["blocks"] += 1; stats["corrected_bytes"] += fixed
            pos = p + 4 + n_cw * N
        except RSDecodeError:
            stats["failed"] += 1
            pos = p + 1
    return frames, stats
