"""How many messages one satellite can carry: a first-order NB-IoT NTN capacity model.

Coverage says when a device can reach a satellite. Capacity says how many devices can use that
pass. Every parameter is illustrative and named so an RF engineer can replace it with lab numbers.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    uplink_tones: int = 48                # 3.75 kHz single-tone slots in one 180 kHz NB-IoT carrier
    tone_rate_bps: float = 500.0          # per tone at the edge of coverage with normal repetitions
    payload_bytes: int = 50               # customer data per message
    overhead_bytes: int = 150             # NB-IoT signalling around it (random access, RRC, NAS, security)
    access_efficiency: float = 0.4        # share of tone-time that carries messages (collisions, guard times, scheduling)
    carriers: int = 1                     # carrier pairs the payload can run at once (downlink power limits this)
    deep_coverage_factor: float = 1.0     # 4.0 = four times the repetitions, a quarter of the throughput

    @property
    def seconds_per_message(self) -> float:
        return (self.payload_bytes + self.overhead_bytes) * 8 / (self.tone_rate_bps / self.deep_coverage_factor)

    @property
    def messages_per_second(self) -> float:
        """Messages one satellite can take per second from the devices in its footprint."""
        return self.carriers * self.uplink_tones * self.access_efficiency / self.seconds_per_message

    def messages_per_day(self, mean_sats_in_view: float) -> float:
        """Daily messages a region can send, given the average number of satellites over it."""
        return self.messages_per_second * 86400 * mean_sats_in_view

    def per_device_per_day(self, devices_in_region: float, mean_sats_in_view: float) -> float:
        return self.messages_per_day(mean_sats_in_view) / devices_in_region
