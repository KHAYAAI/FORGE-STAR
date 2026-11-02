"""Link budgets for the FORGE STAR payload, per elevation angle.

Illustrative parameters for a 6U–12U satellite. Each one is a named field so the
RF engineer can replace it with datasheet values. The question it answers: at
which elevation does each link close, and with what margin? That sets the
elevation mask used in the coverage simulation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

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

    def snr_db(self, el_deg: float, alt_km: float = 550.0) -> float:
        loss = pattern_loss_db(off_nadir_deg(el_deg, alt_km), self.sat_half_beam_deg)
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


# --- Illustrative FORGE STAR links. Replace with datasheet numbers. ---
LINKS = {
    # NB-IoT NTN uplink: 23 dBm device, 0 dBi antenna, single 3.75 kHz tone, deep repetitions.
    "nbiot_uplink": Link("NB-IoT NTN uplink (device→sat), S-band", 2000.0,
                         tx_power_dbw=-7.0, tx_gain_dbi=0.0, rx_gain_dbi=14.0, rx_noise_temp_k=500.0,
                         bandwidth_hz=3750.0, required_snr_db=-8.0, other_losses_db=3.0,
                         sat_side="rx", sat_half_beam_deg=30.0),
    # NB-IoT NTN downlink: ~2 W into a 14 dBi patch array, 180 kHz carrier to a 0 dBi device.
    "nbiot_downlink": Link("NB-IoT NTN downlink (sat→device), S-band", 2185.0,
                           tx_power_dbw=3.0, tx_gain_dbi=14.0, rx_gain_dbi=0.0, rx_noise_temp_k=400.0,
                           bandwidth_hz=180e3, required_snr_db=-6.0, other_losses_db=3.0,
                           sat_side="tx", sat_half_beam_deg=30.0),
    # AIS reception: 12.5 W class A ship, monopole on the satellite. Collisions limit it more than budget.
    "ais_rx": Link("AIS receive (ship→sat), VHF", 162.0,
                   tx_power_dbw=11.0, tx_gain_dbi=2.0, rx_gain_dbi=0.0, rx_noise_temp_k=1500.0,
                   bandwidth_hz=14e3, required_snr_db=8.0, other_losses_db=5.0,
                   sat_side="rx", sat_half_beam_deg=75.0),
    # Feeder/TT&C downlink to the SA gateway: 2 W, 6 dBi patch, 3.7 m dish (~47 dBi at 8.1 GHz).
    "feeder_downlink": Link("Feeder downlink (sat→gateway), X-band", 8100.0,
                            tx_power_dbw=3.0, tx_gain_dbi=6.0, rx_gain_dbi=47.0, rx_noise_temp_k=150.0,
                            bandwidth_hz=10e6, required_snr_db=5.0, other_losses_db=2.0,
                            sat_side="tx", sat_half_beam_deg=60.0),
}


def table(alt_km: float = 550.0, elevations=(5, 10, 20, 30, 45, 60, 90)):
    rows = []
    for key, l in LINKS.items():
        rows.append((l.name, [round(l.margin_db(e, alt_km), 1) for e in elevations], l.min_elevation(3.0, alt_km)))
    return elevations, rows


def with_changes(key: str, **kw) -> Link:
    return replace(LINKS[key], **kw)
