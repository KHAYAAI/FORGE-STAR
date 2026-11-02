# NB-IoT NTN lab test-bed plan

Goal: prove the FORGE STAR payload's radio chain on the bench before anything flies. This is the Stage 0 lab that a TIA/DSI grant funds. All costs are illustrative. Check current hardware prices and the open-source NTN support before buying.

## What the lab must prove

| # | Question | Pass criterion |
|---|---|---|
| 1 | Can a commercial Rel-17 NB-IoT NTN module attach to our network? | Attach + data session through OAI eNB/gNB and Open5GS core |
| 2 | Does it survive LEO Doppler and delay? | Attach and uplink hold with ±48 kHz Doppler at ~2 GHz (S-band MSS) or L-band and ~20 ms one-way delay, as at 550 km and 20° elevation |
| 3 | Does the link budget close? | Uplink decoded at the path loss modelled for a 550 km slant range (~165 dB at 20° elevation) using attenuators |
| 4 | Does store-and-forward work? | Messages buffered "on board" during a simulated pass, delivered to TimescaleDB when the feeder link appears |
| 5 | Can the AIS receiver run beside it? | AIS-catcher decodes injected AIS traffic on the same SDR host without hurting NB-IoT |

## Architecture

```
[NTN NB-IoT module]──coax+attenuators──[Channel emulator: delay + Doppler]──[SDR #1]──[OAI eNB/gNB (NTN)]
                                                                                   │
                                                                     [Open5GS core (EPC/5GC)]
                                                                                   │
                                                           [store-and-forward buffer service]
                                                                                   │
                                                [Kafka iot.uplink → ingest → TimescaleDB]  (ground/docker-compose.yml)
[AIS signal generator / recorded IQ]──[SDR #2]──[AIS-catcher]──────────────────────┘
```

- **Over the air is not allowed** in MSS bands without an ICASA test licence. Everything runs **cabled**, with attenuators and a shielded enclosure. Ask ICASA about a test/experimental licence in the pre-application meeting.
- **Doppler and delay:** start with GNU Radio blocks driven by a Skyfield or `sim/coverage_sim.py` pass profile. Move to a hardware channel emulator later if a grant pays for one.

## Bill of materials (illustrative)

| Item | Qty | Est. cost (USD) | Note |
|---|---|---|---|
| USRP B210 or B205mini (or equivalent) | 2 | 2 × 1,500–2,500 | OAI-supported; one for RAN, one for AIS/monitoring |
| GPSDO / 10 MHz reference | 1 | 300–800 | NTN timing is strict |
| Host PC (8+ cores, low-latency kernel) | 2 | 2 × 1,500 | One RAN, one core + platform |
| Rel-17 NTN NB-IoT dev kits | 2–4 | 100–300 each | Check current vendors and band support |
| Programmable attenuators, cables, splitters, shielded box | 1 set | 1,000–3,000 | |
| Spectrum analyser (entry level) | 1 | 1,500–5,000 | Or borrow from a university or SANSA |
| **Total** | | **~$12–25k** | Fits a seed-stage grant |

## Software

| Layer | Choice | Notes |
|---|---|---|
| RAN | OpenAirInterface with its NTN branch/features | Check the current NB-IoT NTN status in OAI. NR-NTN is more mature. If NB-IoT NTN isn't ready, prove the chain with LTE-M/NR-NTN first |
| Core | Open5GS (EPC for NB-IoT; 5GC for NR) | free5GC as an alternative |
| Channel | GNU Radio + gr-satellites; pass profiles from `sim/coverage_sim.py` | |
| AIS | AIS-catcher | |
| Platform | `ground/docker-compose.yml` | Same pipeline the customers will use |

## 12-week plan

| Weeks | Work | Output |
|---|---|---|
| 1–2 | Buy kit; build OAI + Open5GS; terrestrial NB-IoT attach (no NTN) | Baseline attach log |
| 3–5 | Turn on NTN timing advance, delay and Doppler pre-compensation; static delay first | Attach with 20 ms delay |
| 6–7 | Dynamic Doppler from pass profiles; sweep elevation 10–90° | Attach success vs elevation chart |
| 8–9 | Link-budget sweep with attenuators | Measured sensitivity vs model |
| 10 | Store-and-forward buffer service; deliver into Kafka | End-to-end latency in `latency_hourly` |
| 11 | AIS-catcher on SDR #2 alongside | Decode rate with both running |
| 12 | Write-up for grant body, bus partners and investors | Test report + demo video |

## Risks

- **Open-source NB-IoT NTN maturity.** This is the biggest unknown. Have a fallback ready (NR-NTN or LTE-M) and budget for a commercial stack evaluation licence.
- **Module availability** in the bands we plan to file for. Match the lab band to the ICASA filing plan.
- **Timing and synchronisation** problems cost weeks. Buy the GPSDO on day one.
