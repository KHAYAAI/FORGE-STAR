"""Store-and-forward core logic, free of Kafka so it can be unit-tested."""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from .orbits import RE


@dataclass
class Pending:
    msg: dict
    t_created: float  # sim seconds


@dataclass
class Buffer:
    q: deque = field(default_factory=deque)  # (msg, t_created)


def _visible(sat_ecef: np.ndarray, lat: float, lon: float, mask_deg: float) -> np.ndarray:
    la, lo = math.radians(lat), math.radians(lon)
    up = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
    d = sat_ecef - RE * up
    sin_el = d @ up / np.linalg.norm(d, axis=1)
    return sin_el >= math.sin(math.radians(mask_deg))


def step(sim_t, pending: deque, buffers: dict, sat_ecef: np.ndarray, gw_visible: np.ndarray,
         uplink_mask: float, buffer_cap: int, downlink_budget: int, stats: dict):
    """One tick. Moves messages ground→satellite when a satellite is overhead, and
    satellite→gateway when that satellite sees a gateway. Returns delivered
    [(msg, latency_s, sat_id)]."""
    # 1. uplink: each waiting device message goes to the highest-index visible sat (any is fine)
    keep = deque()
    while pending:
        p = pending.popleft()
        vis = np.flatnonzero(_visible(sat_ecef, p.msg["lat"], p.msg["lon"], uplink_mask))
        if vis.size == 0:
            keep.append(p); continue
        sid = int(vis[0])
        b = buffers[sid]
        if len(b.q) >= buffer_cap:
            stats["dropped_full"] += 1; continue
        b.q.append((p.msg, p.t_created)); stats["uplinked"] += 1
    pending.extend(keep)
    # 2. downlink: satellites over a gateway empty their buffers, oldest first
    out = []
    for sid in np.flatnonzero(gw_visible):
        b = buffers.get(int(sid))
        while b and b.q and downlink_budget > 0:
            msg, t0 = b.q.popleft()
            out.append((msg, sim_t - t0, int(sid))); downlink_budget -= 1
            stats["downlinked"] += 1
    return out
