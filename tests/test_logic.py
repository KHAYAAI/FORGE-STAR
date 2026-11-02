from collections import defaultdict, deque
import numpy as np
from forgestar.logic import Buffer, Pending, step
from forgestar.orbits import RE


def sat_over(lat, lon, alt=550.0):
    import math
    la, lo = math.radians(lat), math.radians(lon)
    return (RE + alt) * np.array([[math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]])


def test_store_then_forward():
    stats = defaultdict(int); buffers = defaultdict(Buffer)
    pending = deque([Pending({"device_id": "pump-0001", "lat": -24.0, "lon": 29.0}, t_created=0.0)])
    # t=100: satellite over the device, not over a gateway -> stored on board
    out = step(100.0, pending, buffers, sat_over(-24.0, 29.0), np.array([False]), 20, 10, 100, stats)
    assert out == [] and not pending and len(buffers[0].q) == 1
    # t=900: satellite over gateway -> delivered with latency 900 s
    out = step(900.0, pending, buffers, sat_over(-25.9, 27.7), np.array([True]), 20, 10, 100, stats)
    assert len(out) == 1 and out[0][1] == 900.0 and out[0][2] == 0


def test_waits_when_no_satellite():
    stats = defaultdict(int); buffers = defaultdict(Buffer)
    pending = deque([Pending({"device_id": "x", "lat": -24.0, "lon": 29.0}, 0.0)])
    step(10.0, pending, buffers, sat_over(30.0, -60.0), np.array([False]), 20, 10, 100, stats)
    assert len(pending) == 1


def test_buffer_full_drops():
    stats = defaultdict(int); buffers = defaultdict(Buffer)
    pending = deque(Pending({"device_id": str(i), "lat": 0.0, "lon": 0.0}, 0.0) for i in range(5))
    step(1.0, pending, buffers, sat_over(0, 0), np.array([False]), 20, 3, 100, stats)
    assert len(buffers[0].q) == 3 and stats["dropped_full"] == 2
