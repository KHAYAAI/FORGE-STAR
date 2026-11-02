import random
import pytest
from forgestar import fec
from forgestar.frames import Frame, Record, decode, short_id



def frame(n=40):
    recs = [Record(short_id(f"pump-{i:04d}"), 1_790_000_000 + i, -24.1, 29.5, {"flow": i}) for i in range(n)]
    return Frame(3, 77, 1_790_000_999, recs).encode()


def test_pn_matches_ccsds_standard():
    assert fec.pn_sequence(8) == bytes.fromhex("FF480EC09A0D70BC")


def test_codewords_have_zero_syndromes():
    # every codeword must evaluate to 0 at all 32 generator roots β^112..β^143
    rnd = random.Random(2)
    for _ in range(20):
        cw = fec.rs_encode(bytes(rnd.randrange(256) for _ in range(223)))
        assert all(fec._poly_eval(list(cw), fec.EXP[(11 * j) % 255]) == 0 for j in range(112, 144))


def test_decoder_stress():
    rnd = random.Random(5)
    for _ in range(200):
        d = bytes(rnd.randrange(256) for _ in range(223)); cw = bytearray(fec.rs_encode(d))
        k = rnd.randrange(0, 17)
        for p in rnd.sample(range(255), k): cw[p] ^= rnd.randrange(1, 256)
        out, fixed = fec.rs_decode(bytes(cw))
        assert out == d and fixed == k
    miscorrect = 0
    for _ in range(100):  # beyond capacity: must be detected, never silently wrong
        d = bytes(rnd.randrange(256) for _ in range(223)); cw = bytearray(fec.rs_encode(d))
        for p in rnd.sample(range(255), 20): cw[p] ^= rnd.randrange(1, 256)
        try:
            out, _ = fec.rs_decode(bytes(cw)); miscorrect += out != d
        except fec.RSDecodeError:
            pass
    assert miscorrect == 0


def test_clean_round_trip_with_noise_around():
    raw = frame()
    stream = bytes(random.Random(3).randrange(256) for _ in range(300)) + fec.encode_block(raw) + b"\x00" * 50
    frames, st = fec.decode_stream(stream)
    assert frames == [raw] and st["corrected_bytes"] == 0
    assert decode(frames[0]).seq == 77


def test_corrects_16_byte_errors_per_codeword():
    raw = frame(); blk = bytearray(fec.encode_block(raw)); rnd = random.Random(4)
    n_cw = (len(blk) - 4) // 255
    for c in range(n_cw):
        for pos in rnd.sample(range(255), 16):
            blk[4 + c * 255 + pos] ^= rnd.randrange(1, 256)
    blk[0] ^= 0x01; blk[2] ^= 0x10  # 2 bit errors in the sync marker too
    frames, st = fec.decode_stream(bytes(blk))
    assert frames == [raw] and st["corrected_bytes"] == 16 * n_cw


def test_too_many_errors_reported_not_raised():
    blk = bytearray(fec.encode_block(frame(5)))
    for pos in range(4, 4 + 40): blk[pos] ^= 0xFF
    frames, st = fec.decode_stream(bytes(blk))
    assert frames == [] and st["failed"] >= 1


def test_back_to_back_blocks():
    a, b = frame(3), frame(60)
    frames, _ = fec.decode_stream(fec.encode_block(a) + fec.encode_block(b))
    assert frames == [a, b]
