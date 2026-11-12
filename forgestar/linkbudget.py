"""Link budgets for the FORGE STAR payload, per elevation angle.

Illustrative parameters for a 6U–12U satellite. Each one is a named field so the
RF engineer can replace it with datasheet values. The question it answers: at
which elevation does each link close, and with what margin? That sets the
elevation mask used in the coverage simulation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from pathlib import Path

from .orbits import RE

K_DBW = -228.6  # Boltzmann constant, dBW/K/Hz


def slant_range_km(el_deg: float, alt_km: float = 550.0) -> float:
    e = math.radians(el_deg); r = RE + alt_km
    return -RE * math.sin(e) + math.sqrt((RE * math.sin(e)) ** 2 + r**2 - RE**2)


def off_nadir_deg(el_deg: float, alt_km: float = 550.0) -> float:
    """Angle at the satellite between nadir and the user."""
    return math.degrees(math.asin(RE * math.cos(math.radians(el_deg)) / (RE + alt_km)))


def pattern_loss_db(off_deg: float, half_beam_deg: float) -> float:
    """cos^q roll-off of a nadir-pointed antenna, -3 dB at half_beam_deg."""
    q = math.log(0.5) / math.log(math.cos(math.radians(half_beam_deg)))
    c = max(math.cos(math.radians(off_deg)), 1e-3)
    return -10 * q * math.log10(c)


def cos_beam_gain_dbi(half_beam_deg: float, efficiency: float = 0.8) -> float:
    """Peak gain of a nadir beam with a cos^q pattern and the given half-power half-angle.

    Directivity of a cos^q(theta) power pattern over one hemisphere is 2(q+1). A wide beam cannot have
    high gain: +/-30 deg gives about 9.7 dBi at 80% efficiency, +/-20 deg about 12.9 dBi.
    """
    q = math.log(0.5) / math.log(math.cos(math.radians(half_beam_deg)))
    return 10 * math.log10(2 * (q + 1) * efficiency)


def half_beam_for_gain_deg(gain_dbi: float, efficiency: float = 0.8) -> float:
    """Half-power half-angle of the cos^q beam that has this peak gain (inverse of cos_beam_gain_dbi)."""
    q = 10 ** (gain_dbi / 10) / (2 * efficiency) - 1
    return math.degrees(math.acos(0.5 ** (1 / q)))


def isoflux_edge_gain_dbi(edge_el_deg: float, alt_km: float = 550.0, efficiency: float = 0.6) -> float:
    """Highest gain an isoflux antenna can have at its edge of coverage.

    The pattern rises with off-nadir angle as (range / edge range)^2 so that every user in the cone sees
    the same signal. Its total radiated power is fixed, which bounds the edge gain:
    G_edge = 4*pi*efficiency / integral of the pattern over the cone.
    """
    edge_off = math.radians(off_nadir_deg(edge_el_deg, alt_km))
    r_edge = slant_range_km(edge_el_deg, alt_km)
    n, total = 2000, 0.0
    for i in range(n):
        th = (i + 0.5) / n * edge_off
        # elevation seen by a user at this off-nadir angle
        el = math.degrees(math.acos(min(1.0, (RE + alt_km) / RE * math.sin(th))))
        total += (slant_range_km(el, alt_km) / r_edge) ** 2 * math.sin(th) * edge_off / n
    return 10 * math.log10(4 * math.pi * efficiency / (2 * math.pi * total))


def fspl_db(range_km: float, f_mhz: float) -> float:
    return 20 * math.log10(range_km) + 20 * math.log10(f_mhz) + 32.45


@dataclass(frozen=True)
class Link:
    name: str
    f_mhz: float
    tx_power_dbw: float
    tx_gain_dbi: float
    rx_gain_dbi: float
    rx_noise_temp_k: float
    bandwidth_hz: float
    required_snr_db: float   # incl. implementation loss for the modulation/coding used
    other_losses_db: float   # polarisation, pointing, atmosphere, body loss
    rx_line_loss_db: float = 1.0
    sat_side: str = "rx"          # which end is the nadir-pointed satellite antenna
    sat_half_beam_deg: float = 30.0
    # Satellite antenna pattern: "cos" (fixed nadir beam), "isoflux" (shaped: peak gain at the
    # edge of coverage to cancel the longer range), "array" (electronically steered, scan loss)
    sat_pattern: str = "cos"
    edge_el_deg: float = 20.0      # isoflux: elevation where gain peaks (edge of coverage)
    max_scan_deg: float = 60.0     # array: beyond this the beam can't be steered

    def sat_gain_loss_db(self, el_deg: float, alt_km: float = 550.0) -> float:
        """dB below the satellite antenna's peak gain toward a user at this elevation."""
        off = off_nadir_deg(el_deg, alt_km)
        if self.sat_pattern == "isoflux":
            edge_off = off_nadir_deg(self.edge_el_deg, alt_km)
            if off > edge_off:  # outside the shaped beam: fast roll-off
                return pattern_loss_db(off - edge_off, 8.0)
            return 20 * math.log10(slant_range_km(self.edge_el_deg, alt_km) / slant_range_km(el_deg, alt_km))
        if self.sat_pattern == "array":
            if off > self.max_scan_deg:
                return 30.0
            return -10 * 1.3 * math.log10(max(math.cos(math.radians(off)), 1e-3))  # cos^1.3 scan loss
        return pattern_loss_db(off, self.sat_half_beam_deg)

    @property
    def sat_gain_dbi(self) -> float:
        return self.rx_gain_dbi if self.sat_side == "rx" else self.tx_gain_dbi

    def gain_limit_dbi(self, alt_km: float = 550.0) -> float | None:
        """Most gain the satellite antenna can have for its beam shape (None for a steered array)."""
        if self.sat_pattern == "cos":
            return cos_beam_gain_dbi(self.sat_half_beam_deg)
        if self.sat_pattern == "isoflux":
            return isoflux_edge_gain_dbi(self.edge_el_deg, alt_km)
        return None

    def gain_is_consistent(self, alt_km: float = 550.0, tol_db: float = 0.5) -> bool:
        lim = self.gain_limit_dbi(alt_km)
        return lim is None or self.sat_gain_dbi <= lim + tol_db

    def snr_db(self, el_deg: float, alt_km: float = 550.0) -> float:
        loss = self.sat_gain_loss_db(el_deg, alt_km)
        tx_g = self.tx_gain_dbi - (loss if self.sat_side == "tx" else 0)
        rx_g = self.rx_gain_dbi - (loss if self.sat_side == "rx" else 0)
        eirp = self.tx_power_dbw + tx_g
        g_t = rx_g - self.rx_line_loss_db - 10 * math.log10(self.rx_noise_temp_k)
        c_n0 = eirp - fspl_db(slant_range_km(el_deg, alt_km), self.f_mhz) - self.other_losses_db + g_t - K_DBW
        return c_n0 - 10 * math.log10(self.bandwidth_hz)

    def margin_db(self, el_deg: float, alt_km: float = 550.0) -> float:
        return self.snr_db(el_deg, alt_km) - self.required_snr_db

    def min_elevation(self, margin_needed_db: float = 3.0, alt_km: float = 550.0) -> float | None:
        """Lowest elevation (deg) where the link closes with the required margin, or None."""
        for e10 in range(0, 901):
            if self.margin_db(e10 / 10, alt_km) >= margin_needed_db:
                return e10 / 10
        return None


# --- Link parameters come from forgestar/params/rf.yaml (value + source + status per field). ---
PARAMS_FILE = Path(__file__).parent / "params" / "rf.yaml"


def load_links(path: Path = PARAMS_FILE) -> dict[str, Link]:
    import yaml
    raw = yaml.safe_load(path.read_text())
    out = {}
    for key, spec in raw.items():
        kw = {k: (v["value"] if isinstance(v, dict) else v) for k, v in spec.items()}
        out[key] = Link(**kw)
    return out


def param_status(path: Path = PARAMS_FILE) -> list[tuple[str, str, object, str, str]]:
    """(link, field, value, status, source) for every parameter, for the verification register."""
    import yaml
    rows = []
    for key, spec in yaml.safe_load(path.read_text()).items():
        for f, v in spec.items():
            if isinstance(v, dict):
                rows.append((key, f, v["value"], v.get("status", "illustrative"), v.get("source", "")))
    return rows


LINKS = load_links()


def table(alt_km: float = 550.0, elevations=(5, 10, 20, 30, 45, 60, 90)):
    rows = []
    for key, l in LINKS.items():
        rows.append((l.name, [round(l.margin_db(e, alt_km), 1) for e in elevations], l.min_elevation(3.0, alt_km)))
    return elevations, rows


def with_changes(key: str, **kw) -> Link:
    return replace(LINKS[key], **kw)
