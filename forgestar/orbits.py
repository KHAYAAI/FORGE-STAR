"""Orbit propagation and visibility for FORGE STAR constellations.

Circular orbits with J2 secular effects (nodal regression and the argument-of-
latitude rate correction). That is the dominant perturbation for constellation
geometry over days to weeks; drag and higher harmonics change phasing slowly and
are left to Orekit for mission-grade work.

Shared by sim/, the store-and-forward service in ground/sandf and the tests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

RE = 6378.137           # km, WGS-84 equatorial radius
MU = 398600.4418        # km^3/s^2
J2 = 1.08262668e-3
OMEGA_E = 7.2921159e-5  # rad/s


@dataclass(frozen=True)
class Site:
    name: str
    region: str
    lat: float  # deg
    lon: float  # deg


@dataclass
class Constellation:
    """Walker-delta i:T/P/F. inc_deg=None alternates 45° and 97.6° (SSO) planes."""
    n: int
    planes: int
    inc_deg: float | None
    alt_km: float = 550.0
    phasing: int = 1
    label: str = ""

    def elements(self):
        per = self.n // self.planes
        inc, raan, u0 = [], [], []
        for p in range(self.planes):
            i = (45.0 if p % 2 == 0 else 97.6) if self.inc_deg is None else self.inc_deg
            for k in range(per):
                inc.append(math.radians(i))
                raan.append(2 * math.pi * p / self.planes)
                u0.append(2 * math.pi * k / per + 2 * math.pi * self.phasing * p / self.n)
        for k in range(self.n - per * self.planes):  # leftovers into plane 0, interleaved
            inc.append(math.radians(self.inc_deg or 45.0)); raan.append(0.0)
            u0.append(2 * math.pi * (k + 0.5) / max(per, 1))
        return np.array(inc), np.array(raan), np.array(u0)


def j2_rates(alt_km: float, inc: np.ndarray):
    """Secular rates (rad/s): RAAN drift and argument-of-latitude rate for circular orbits."""
    a = RE + alt_km
    n = math.sqrt(MU / a**3)
    k = 1.5 * J2 * (RE / a) ** 2 * n
    raan_dot = -k * np.cos(inc)
    u_dot = n + k * (4 * np.cos(inc) ** 2 - 1)  # = n + (dω/dt + dM/dt − n) for e=0
    return raan_dot, u_dot


def propagate_eci(c: Constellation, t: np.ndarray, j2: bool = True) -> np.ndarray:
    """Satellite inertial positions (km), shape (T, N, 3), for times t (s from epoch)."""
    inc, raan0, u0 = c.elements()
    if j2:
        raan_dot, u_dot = j2_rates(c.alt_km, inc)
    else:
        raan_dot = np.zeros_like(inc); u_dot = np.full_like(inc, math.sqrt(MU / (RE + c.alt_km) ** 3))
    r = RE + c.alt_km
    u = u0[None, :] + u_dot[None, :] * t[:, None]
    O = raan0[None, :] + raan_dot[None, :] * t[:, None]
    ci, si = np.cos(inc), np.sin(inc)
    x = r * (np.cos(O) * np.cos(u) - np.sin(O) * np.sin(u) * ci)
    y = r * (np.sin(O) * np.cos(u) + np.cos(O) * np.sin(u) * ci)
    z = r * (np.sin(u) * si) * np.ones_like(O)
    return np.stack([x, y, z], -1)


def propagate_ecef(c: Constellation, t: np.ndarray, j2: bool = True, gmst0: float = 0.0) -> np.ndarray:
    """Satellite Earth-fixed positions (km), shape (T, N, 3). gmst0 = Earth rotation angle at epoch (rad)."""
    p = propagate_eci(c, t, j2)
    th = (gmst0 + OMEGA_E * t)[:, None]
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return np.stack([np.cos(th) * x + np.sin(th) * y, -np.sin(th) * x + np.cos(th) * y, z], -1)


def site_vectors(sites):
    lat = np.radians([s.lat for s in sites]); lon = np.radians([s.lon for s in sites])
    up = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)
    return RE * up, up


def look(sat_ecef: np.ndarray, sites):
    """Elevation (deg) and slant range (km), shape (T, P, N)."""
    g, up = site_vectors(sites)
    d = sat_ecef[:, None, :, :] - g[None, :, None, :]
    rng = np.linalg.norm(d, axis=-1)
    el = np.degrees(np.arcsin(np.clip(np.einsum("tpnk,pk->tpn", d, up) / rng, -1, 1)))
    return el, rng


@dataclass
class Pass:
    sat: int
    site: str
    start: float
    end: float
    max_el: float
    min_range_km: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def find_passes(c: Constellation, sites, t: np.ndarray, min_el: float = 10.0, j2: bool = True) -> list[Pass]:
    """All passes above min_el for every (site, satellite) pair in the time grid."""
    el, rng = look(propagate_ecef(c, t, j2), sites)
    out = []
    for p, s in enumerate(sites):
        for n in range(el.shape[2]):
            vis = el[:, p, n] >= min_el
            if not vis.any():
                continue
            edges = np.diff(vis.astype(int))
            starts = list(np.where(edges == 1)[0] + 1); ends = list(np.where(edges == -1)[0] + 1)
            if vis[0]: starts.insert(0, 0)
            if vis[-1]: ends.append(len(t))
            for a, b in zip(starts, ends):
                out.append(Pass(n, s.name, float(t[a]), float(t[b - 1]),
                                float(el[a:b, p, n].max()), float(rng[a:b, p, n].min())))
    return sorted(out, key=lambda x: x.start)
