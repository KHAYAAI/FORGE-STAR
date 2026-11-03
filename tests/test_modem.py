import sys
from pathlib import Path
import numpy as np
from forgestar import fec, modem
from forgestar.frames import Frame, Record, short_id

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ground" / "gateway"))


def block():
    recs = [Record(short_id(f"pump-{i:04d}"), 1_790_000_000 + i, -24.1, 29.5, {"flow": i}) for i in range(30)]
    raw = Frame(3, 7, 1_790_000_999, recs).encode()
    return raw, fec.encode_block(raw)


def test_clean_round_trip():
    raw, blk = block()
    assert fec.decode_stream(modem.demodulate(modem.channel(modem.modulate(blk), 40)))[0] == [raw]


def test_rs_only_at_6db_with_doppler_phase_timing():
    raw, blk = block(); x = modem.modulate(blk, coded=False)
    for trial in range(4):
        rng = np.random.default_rng(trial)
        y = modem.channel(x, 6.0, freq_offset=rng.uniform(-0.004, 0.004), phase=rng.uniform(0, 6.28),
                          delay=int(rng.integers(0, 50)), rng=rng, code_rate_inv=1)
        frames, st = fec.decode_stream(modem.demodulate(y, coded=False))
        assert frames == [raw] and st["corrected_bytes"] > 0      # RS is doing real work at this SNR


def test_concatenated_code_at_2_5db():
    """RS + convolutional code works ~3.5 dB below where RS alone fails."""
    raw, blk = block(); x = modem.modulate(blk)
    for trial in range(4):
        rng = np.random.default_rng(10 + trial)
        y = modem.channel(x, 2.5, freq_offset=rng.uniform(-0.004, 0.004), phase=rng.uniform(0, 6.28),
                          delay=int(rng.integers(0, 50)), rng=rng)
        assert fec.decode_stream(modem.demodulate(y))[0] == [raw]
    xu = modem.modulate(blk, coded=False)
    yu = modem.channel(xu, 2.5, rng=np.random.default_rng(1), code_rate_inv=1)
    assert fec.decode_stream(modem.demodulate(yu, coded=False))[0] == []


def test_viterbi_clean_and_matches_encoder():
    from forgestar import conv
    bits = np.random.default_rng(5).integers(0, 2, 500).astype(np.uint8)
    dec, _ = conv.viterbi(1.0 - 2.0 * conv.encode_bits(bits))
    assert np.array_equal(dec, bits)


def test_gateway_reads_iq_recordings(tmp_path):
    import gateway as gwmod
    raw, blk = block()
    y = modem.channel(modem.modulate(blk), 10, freq_offset=0.001, phase=0.7, rng=np.random.default_rng(3))
    y.astype(np.complex64).tofile(tmp_path / "pass-001.cf32")
    out = []; g = gwmod.Gateway(out.append, lambda s: None)
    gwmod.scan_dir(g, tmp_path)
    assert len(out) == 30 and (tmp_path / "done" / "pass-001.cf32").exists()
