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


# ---------------------------------------------------------------------------
# Re-send until acknowledged (the policy sim/latency_sim.py shows is needed)
# ---------------------------------------------------------------------------
from collections import OrderedDict  # noqa: E402

from .frames import short_id  # noqa: E402


def msg_key(msg: dict) -> tuple[int, int]:
    """Identity of a device message across copies: (device short id, device timestamp)."""
    return short_id(msg["device_id"]), int(msg["ts"])


class ResendNetwork:
    """Devices keep each message until acked; every satellite overhead takes a copy.
    Acks come from the ground (gateway) via `queue_ground_acks`, reach satellites when they
    pass a gateway, and reach devices when an acked satellite is overhead again."""

    ACK_MEMORY = 200_000

    def __init__(self, buffer_cap: int):
        self.cap = buffer_cap
        self.pending: dict[tuple[int, int], Pending] = {}        # on devices, not yet acked
        self.carried: dict[tuple[int, int], set[int]] = {}        # which satellites hold a copy
        self.buf: dict[int, OrderedDict] = {}                     # sat -> key -> (msg, t_created)
        self.sat_acks: dict[int, OrderedDict] = {}                # sat -> acked keys it knows
        self.uplink: list = []                                    # append-only ack log held at the gateways
        self._queued: set = set()
        self.sat_seen: dict[int, int] = {}                        # how far each satellite has read the log

    def add(self, msg: dict, t_created: float):
        k = msg_key(msg)
        if k not in self.pending:
            self.pending[k] = Pending(msg, t_created); self.carried[k] = set()

    def queue_ground_acks(self, keys):
        for k in keys:
            k = tuple(k)
            if k not in self._queued:
                self._queued.add(k); self.uplink.append(k)
        if len(self.uplink) > 2 * self.ACK_MEMORY:                # trim the log, keep satellites' read positions valid
            cut = len(self.uplink) - self.ACK_MEMORY
            for k in self.uplink[:cut]: self._queued.discard(k)
            self.uplink = self.uplink[cut:]
            self.sat_seen = {s: max(0, i - cut) for s, i in self.sat_seen.items()}

    def _sat_knows(self, s: int, k) -> bool:
        a = self.sat_acks.get(s)
        return bool(a) and k in a

    def step(self, sim_t, sat_ecef, gw_visible, uplink_mask, downlink_budget, stats):
        out = []
        # 1. satellites over a gateway: receive the ground's ack list, drop acked copies, downlink the rest
        for s in np.flatnonzero(gw_visible):
            s = int(s)
            known = self.sat_acks.setdefault(s, OrderedDict())
            start = max(self.sat_seen.get(s, 0), len(self.uplink) - self.ACK_MEMORY)
            for k in self.uplink[start:]:
                known[k] = True
            self.sat_seen[s] = len(self.uplink)
            while len(known) > self.ACK_MEMORY: known.popitem(last=False)
            b = self.buf.get(s)
            while b and downlink_budget > 0:
                k, (msg, t0) = b.popitem(last=False)
                if k in known:
                    stats["dropped_acked_onboard"] += 1; continue
                out.append((msg, sim_t - t0, s)); downlink_budget -= 1; stats["downlinked"] += 1
        # 2. devices: hear acks from satellites overhead, otherwise hand copies to new satellites
        by_pos: dict[tuple[float, float], list] = {}
        for k, p in self.pending.items():
            by_pos.setdefault((p.msg["lat"], p.msg["lon"]), []).append(k)
        done = []
        for (lat, lon), keys in by_pos.items():
            vis = [int(s) for s in np.flatnonzero(_visible(sat_ecef, lat, lon, uplink_mask))]
            if not vis:
                continue
            for k in keys:
                if any(self._sat_knows(s, k) for s in vis):
                    done.append(k); continue
                for s in vis:
                    if s in self.carried[k]:
                        continue
                    b = self.buf.setdefault(s, OrderedDict())
                    if len(b) >= self.cap:
                        stats["dropped_full"] += 1; continue
                    b[k] = (self.pending[k].msg, self.pending[k].t_created)
                    self.carried[k].add(s); stats["uplinked"] += 1
        for k in done:
            del self.pending[k]; del self.carried[k]; stats["acked_on_device"] += 1
        # 3. satellites not at a gateway still drop copies they already know were acked
        for s, b in self.buf.items():
            known = self.sat_acks.get(s)
            if known and b:
                for k in [k for k in b if k in known]:
                    del b[k]; stats["dropped_acked_onboard"] += 1
        return out
